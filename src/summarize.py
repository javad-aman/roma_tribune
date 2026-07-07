"""
Translate, filter, and summarize gathered items via a single Claude Haiku call.

One API call per run: send all raw items, get back the top 15 translated +
summarized + classified items. No batching, no second filter pass.

Usage:
    python -m src.summarize --input data/gather.json
    python -m src.summarize --input data/gather.json --output data/summarized.json
"""

import argparse
import json
import os
import pathlib

import anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = pathlib.Path(__file__).parent.parent
MODEL = "claude-haiku-4-5-20251001"
MAX_ITEMS = 15
# Truncate raw snippet per item to keep the prompt from bloating
MAX_SNIPPET_CHARS = 300


def load_items(path: str) -> list[dict]:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _build_prompt(items: list[dict]) -> str:
    block = ""
    for i, item in enumerate(items, 1):
        snippet = (item.get("summary") or "")[:MAX_SNIPPET_CHARS]
        block += (
            f"\nItem {i}:\n"
            f"  Language: {item.get('language', 'en')}\n"
            f"  Source: {item.get('source', '')}\n"
            f"  Date: {item.get('date', '')}\n"
            f"  Headline: {item.get('headline', '')}\n"
            f"  Snippet: {snippet or '(none)'}\n"
        )

    return f"""You are the editor of Roma Tribune, an English-language AS Roma newsletter.

You have {len(items)} raw news items gathered today. In ONE pass:
1. Identify the {MAX_ITEMS} most important and newsworthy stories. Drop minor, repetitive, or low-value items.
   Prioritize: confirmed transfers, match results, manager/contract news, major club decisions.
   De-prioritize: vague rumors, celebrity cameos, unrelated football, social media fluff.
2. If multiple items cover the same story, MERGE them into one richer item.
3. Translate headline and summary to English if the source language is "it".
4. Write a clean 2-3 sentence English summary of the key facts. Do NOT invent details not present in the snippet.
5. Classify into exactly one section: "Transfers", "Match & Results", or "Club & Other".

Return a JSON array of up to {MAX_ITEMS} items. No markdown fences, no commentary. Schema:
{{"headline": "<str>", "summary": "<str>", "section": "<Transfers|Match & Results|Club & Other>", "source": "<str>", "date": "<str>"}}

Items:{block}"""


def _parse_response(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def summarize_all(items: list[dict]) -> list[dict]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found — add it to your .env file")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"  Sending {len(items)} raw items to {MODEL} (1 call)...", end=" ", flush=True)
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": _build_prompt(items)}],
    )
    result = _parse_response(message.content[0].text)
    print(f"done ({len(result)} items kept)")
    return result


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
