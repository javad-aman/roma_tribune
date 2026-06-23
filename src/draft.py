"""
Assemble a Roma Tribune newsletter draft from summarized items.

Reads the summarized digest, optionally filters against the covered log,
then calls Claude to produce a ready-to-edit Markdown draft.

Usage:
    python -m src.draft --opinion "Why selling Dovbyk now is a mistake"
    python -m src.draft --opinion "..." --input data/summarized.json --output data/draft.md
    python -m src.draft --opinion "..." --covered content/covered-log.md
"""

import argparse
import json
import os
import pathlib
from datetime import date

import anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = pathlib.Path(__file__).parent.parent
MODEL = "claude-haiku-4-5-20251001"
SECTIONS = ["Transfers", "Match & Results", "Club & Other"]


def load_items(path: str) -> list[dict]:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def load_covered_log(path: str) -> str:
    p = pathlib.Path(path)
    if not p.exists():
        return "(no covered log provided)"
    return p.read_text(encoding="utf-8")


def _format_digest(items: list[dict]) -> str:
    """Format items into a structured digest string for the prompt."""
    sections: dict[str, list[dict]] = {s: [] for s in SECTIONS}
    for item in items:
        section = item.get("section", "Club & Other")
        if section not in sections:
            section = "Club & Other"
        sections[section].append(item)

    lines = []
    for section, entries in sections.items():
        if not entries:
            continue
        lines.append(f"\n### {section}\n")
        for e in entries:
            lines.append(f"**{e['headline']}** [{e['reliability']}]")
            lines.append(f"{e['summary']}")
            lines.append(f"*Source: {e['source']} — {e['date']}*\n")
    return "\n".join(lines)


def _build_prompt(digest: str, covered_log: str, opinion_angle: str, issue_date: str) -> str:
    return f"""You are writing a Roma Tribune newsletter issue — an independent, English-language newsletter about AS Roma for diaspora fans.

VOICE: Opinionated, not neutral wire-copy. Take clear positions. Write as a lifelong Roma fan who knows the game. Punchy sentences. No corporate hedging.

FACTS RULE — THIS IS MANDATORY: Every specific number, fee, score, date, or statistic you write must come directly from the digest provided below. Do NOT use your training knowledge to fill in transfer fees, contract values, match scores, or any other figures not explicitly stated in the digest. If a number is not in the digest, omit it entirely rather than guess or recall it. Violating this rule produces misinformation that will be published to real readers.

STRUCTURE — write exactly this, in Markdown:

# Roma Tribune — {issue_date}

## This Week

[2-3 sentence intro: set the mood of the week, lead with the biggest story or theme. Personal tone.]

---

## Transfers

[For each transfer item: bold headline, 2-3 sentence write-up with your take, reliability label. Skip items with no meaningful content. Group related stories.]

---

## Match & Results

[Match coverage with score, key moments, brief tactical or player observation. If no matches this week, write "No competitive action this week."]

---

## Club & Other

[Club news, injuries, off-pitch stories. Same format: bold headline, 2-3 sentences, your angle.]

---

## [Opinion section title — make it punchy]

[400-600 words on the angle below. One clear argument. Back it with specifics from the digest where relevant. End with a clear conclusion, not a hedge.]

---

*Roma Tribune is an independent newsletter. If someone forwarded this to you, subscribe here.*

---

ALREADY COVERED (skip these unless the digest marks them as an UPDATE):
{covered_log}

---

THIS WEEK'S DIGEST:
{digest}

---

OPINION ANGLE FOR THIS ISSUE:
{opinion_angle}

Write the full issue now. Do not add any commentary before or after the Markdown."""


def draft(items: list[dict], opinion_angle: str, covered_log: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found — add it to your .env file")

    client = anthropic.Anthropic(api_key=api_key)
    issue_date = date.today().strftime("%B %d, %Y")
    digest = _format_digest(items)

    print(f"  Digest: {len(items)} items across {sum(1 for s in SECTIONS if any(i.get('section')==s for i in items))} sections")
    print(f"  Opinion angle: {opinion_angle}")
    print(f"  Model: {MODEL}")
    print("  Calling Claude...", end=" ", flush=True)

    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": _build_prompt(digest, covered_log, opinion_angle, issue_date),
        }],
    )

    print("done")
    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Generate a Roma Tribune newsletter draft")
    parser.add_argument("--opinion", required=True, help="Angle for the opinion/match-review section")
    parser.add_argument("--input", default="data/summarized.json", help="Summarized items JSON")
    parser.add_argument("--covered", default="content/covered-log.md", help="Covered story log")
    parser.add_argument("--output", default="data/draft.md", help="Output Markdown file")
    args = parser.parse_args()

    print("Drafting Roma Tribune issue...\n")

    items = load_items(args.input)
    covered_log = load_covered_log(args.covered)
    text = draft(items, args.opinion, covered_log)

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    print(f"\nDraft saved to {out}")
    print("Open it, edit it, then paste into Substack.")


if __name__ == "__main__":
    main()
