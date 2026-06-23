"""
Gather AS Roma news from multiple sources:
  - Direct RSS feeds (Forzaroma, RomaNews, etc.)
  - Google News RSS (covers Italian + English press with no API key)
  - Reddit r/asroma RSS
  - NewsAPI (English outlets, requires NEWS_API_KEY in .env)

Usage:
    python -m src.gather --start 2026-06-16 --end 2026-06-22
    python -m src.gather --start 2026-06-16 --end 2026-06-22 --output data/gather.json
"""

import argparse
import json
import os
import pathlib
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = pathlib.Path(__file__).parent.parent
SOURCES_FILE = ROOT / "src" / "config" / "sources.yaml"

GOOGLE_NEWS_QUERIES = [
    # Italian — covers Corriere, Gazzetta, Il Romanista, Forzaroma, etc.
    ("AS Roma", "it", "IT", "it"),
    ("Roma calciomercato", "it", "IT", "it"),
    # English
    ("AS Roma", "en", "US", "en"),
]

REDDIT_RSS = "https://www.reddit.com/r/asroma/.rss"

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"
NEWSAPI_QUERIES = ["AS Roma", "Roma Serie A"]


def load_sources() -> list[dict]:
    """Return all sources that have an RSS feed configured."""
    with open(SOURCES_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sources = []
    for category, entries in data.items():
        if category == "transfer_reporters":
            continue
        for entry in entries:
            if entry.get("rss"):
                sources.append({
                    "name": entry["name"],
                    "rss": entry["rss"],
                    "language": entry.get("language", "en"),
                })
    return sources


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def _make_item(headline, url, summary, source, language, pub) -> dict:
    return {
        "headline": _strip_html(headline).strip(),
        "url": url,
        "summary": _strip_html(summary).strip(),
        "source": source,
        "language": language,
        "date": pub.strftime("%Y-%m-%d"),
        "section": "Club & Other",  # re-classified by summarize.py
    }


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def fetch_direct_rss(source: dict, start: datetime, end: datetime) -> list[dict]:
    """Fetch a direct RSS feed (Forzaroma, RomaNews, etc.)."""
    feed = feedparser.parse(source["rss"])
    items = []
    for entry in feed.entries:
        pub = _parse_date(entry)
        if pub is None or not (start <= pub <= end):
            continue
        items.append(_make_item(
            entry.get("title", ""),
            entry.get("link", ""),
            entry.get("summary", ""),
            source["name"],
            source["language"],
            pub,
        ))
    return items


def fetch_google_news(start: datetime, end: datetime) -> list[dict]:
    """
    Query Google News RSS for AS Roma coverage.
    No API key needed. Returns results from all indexed outlets.
    """
    items = []
    for query, hl, gl, lang in GOOGLE_NEWS_QUERIES:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
        )
        feed = feedparser.parse(url)
        for entry in feed.entries:
            pub = _parse_date(entry)
            if pub is None or not (start <= pub <= end):
                continue
            # Google News titles are "Headline - Source Name"
            title = entry.get("title", "")
            source_name = "Google News"
            if " - " in title:
                *parts, outlet = title.rsplit(" - ", 1)
                title = " - ".join(parts)
                source_name = outlet
            items.append(_make_item(
                title,
                entry.get("link", ""),
                entry.get("summary", ""),
                source_name,
                lang,
                pub,
            ))
    return items


def fetch_reddit(start: datetime, end: datetime) -> list[dict]:
    """Fetch r/asroma RSS — good for English fan discussion and breaking links."""
    headers = {"User-Agent": "roma-tribune/1.0"}
    feed = feedparser.parse(REDDIT_RSS, request_headers=headers)
    items = []
    for entry in feed.entries:
        pub = _parse_date(entry)
        if pub is None or not (start <= pub <= end):
            continue
        items.append(_make_item(
            entry.get("title", ""),
            entry.get("link", ""),
            entry.get("summary", ""),
            "r/asroma",
            "en",
            pub,
        ))
    return items


def fetch_newsapi(start: datetime, end: datetime) -> list[dict]:
    """
    Fetch English-language coverage via NewsAPI free tier.
    Requires NEWS_API_KEY in .env. Skipped silently if key is absent.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []

    items = []
    for query in NEWSAPI_QUERIES:
        params = {
            "q": query,
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": api_key,
        }
        try:
            resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=10)
            resp.raise_for_status()
            for article in resp.json().get("articles", []):
                pub_str = article.get("publishedAt", "")
                try:
                    pub = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue
                if not (start <= pub <= end):
                    continue
                items.append(_make_item(
                    article.get("title", ""),
                    article.get("url", ""),
                    article.get("description", ""),
                    article.get("source", {}).get("name", "NewsAPI"),
                    "en",
                    pub,
                ))
        except requests.RequestException as exc:
            print(f"  NewsAPI ({query}): FAILED — {exc}")
    return items


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate(items: list[dict]) -> list[dict]:
    """
    Two-pass dedup:
    1. Exact URL match (keeps first seen).
    2. Near-duplicate headlines (Jaccard on word sets, threshold 0.8).
    Google News and direct RSS often carry the same story.
    """
    # Pass 1: URL
    seen_urls: set[str] = set()
    url_unique: list[dict] = []
    for item in items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            url_unique.append(item)

    # Pass 2: headline similarity
    def _words(text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    kept: list[dict] = []
    seen_headlines: list[set[str]] = []
    for item in url_unique:
        words = _words(item["headline"])
        duplicate = False
        for seen in seen_headlines:
            if not words or not seen:
                continue
            jaccard = len(words & seen) / len(words | seen)
            if jaccard >= 0.8:
                duplicate = True
                break
        if not duplicate:
            kept.append(item)
            seen_headlines.append(words)
    return kept


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def gather(start: datetime, end: datetime) -> list[dict]:
    all_items: list[dict] = []

    print("Direct RSS feeds:")
    for source in load_sources():
        try:
            items = fetch_direct_rss(source, start, end)
            all_items.extend(items)
            print(f"  {source['name']}: {len(items)} item(s)")
        except Exception as exc:
            print(f"  {source['name']}: FAILED — {exc}")

    print("\nGoogle News RSS:")
    try:
        items = fetch_google_news(start, end)
        all_items.extend(items)
        print(f"  {len(items)} item(s) across all queries")
    except Exception as exc:
        print(f"  FAILED — {exc}")

    print("\nReddit r/asroma:")
    try:
        items = fetch_reddit(start, end)
        all_items.extend(items)
        print(f"  {len(items)} item(s)")
    except Exception as exc:
        print(f"  FAILED — {exc}")

    print("\nNewsAPI:")
    try:
        items = fetch_newsapi(start, end)
        if items:
            all_items.extend(items)
            print(f"  {len(items)} item(s)")
        else:
            print("  skipped (no NEWS_API_KEY in .env)")
    except Exception as exc:
        print(f"  FAILED — {exc}")

    deduped = deduplicate(all_items)
    return deduped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gather AS Roma news")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--output", help="Write JSON to this path (default: print)")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    print(f"Gathering AS Roma news: {args.start} to {args.end}\n")
    items = gather(start, end)
    print(f"\nTotal after deduplication: {len(items)} item(s)\n")

    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved to {out}")
    else:
        print(json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
