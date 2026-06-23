"""
Translate Italian items and summarize all items via Claude Haiku (Anthropic API).

Each item gets:
  - headline translated to English (if Italian)
  - 2-3 sentence English summary
  - section classification: Transfers | Match & Results | Club & Other
  - reliability flag: confirmed | reported | rumor

Usage:
    python -m src.summarize --input data/gather.json
    python -m src.summarize --input data/gather.json --output data/summarized.json
"""

import argparse
import json
import os
import pathlib
import time

import anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = pathlib.Path(__file__).parent.parent
MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 15
BATCH_SLEEP_SECONDS = 1  # Haiku is fast; minimal sleep needed


def load_items(path: str) -> list[dict]:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _build_prompt(batch: list[dict]) -> str:
    block = ""
    for i, item in enumerate(batch, 1):
        block += (
            f"\nItem {i}:\n"
            f"  Language: {item['language']}\n"
            f"  Source: {item['source']}\n"
            f"  Headline: {item['headline']}\n"
            f"  Raw text: {item['summary'] or '(none)'}\n"
        )

    return f"""You are processing AS Roma football news for an English-language newsletter.

For each item:
1. Translate headline and summary to English if the language is "it".
2. Write a clean 2-3 sentence summary of the key facts. Do not invent details.
3. Classify into exactly one section: "Transfers", "Match & Results", or "Club & Other".
4. Assign reliability: "confirmed" (official/announced), "reported" (credible sourcing), "rumor" (unverified).

Return a JSON array only — no markdown fences, no commentary. Schema per element:
{{"index": <int>, "headline": "<str>", "summary": "<str>", "section": "<str>", "reliability": "<str>"}}

Items:{block}"""


def _parse_response(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def summarize_batch(batch: list[dict], client: anthropic.Anthropic) -> list[dict]:
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": _build_prompt(batch)}],
    )
    results = _parse_response(message.content[0].text)

    enriched = []
    for result in results:
        idx = result["index"] - 1
        if not (0 <= idx < len(batch)):
            continue
        enriched.append({
            **batch[idx],
            "headline": result["headline"],
            "summary": result["summary"],
            "section": result["section"],
            "reliability": result["reliability"],
        })
    return enriched


def summarize_all(items: list[dict]) -> list[dict]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found — add it to your .env file")

    client = anthropic.Anthropic(api_key=api_key)
    batches = [items[i : i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
    all_enriched: list[dict] = []

    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}/{len(batches)} ({len(batch)} items)...", end=" ", flush=True)
        try:
            enriched = summarize_batch(batch, client)
            all_enriched.extend(enriched)
            print(f"done ({len(enriched)} processed)")
        except Exception as exc:
            print(f"FAILED: {exc} -- keeping raw items")
            all_enriched.extend(batch)

        if i < len(batches):
            time.sleep(BATCH_SLEEP_SECONDS)

    return all_enriched


def main():
    parser = argparse.ArgumentParser(description="Translate + summarize gathered items")
    parser.add_argument("--input", default="data/gather.json")
    parser.add_argument("--output", default="data/summarized.json")
    args = parser.parse_args()

    items = load_items(args.input)
    print(f"Summarizing {len(items)} items via {MODEL}...\n")

    enriched = summarize_all(items)

    from collections import Counter
    counts = Counter(item.get("section", "unknown") for item in enriched)
    print("\nSection breakdown:")
    for section, count in sorted(counts.items()):
        print(f"  {section}: {count}")

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
