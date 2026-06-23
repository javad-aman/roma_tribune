"""
Gather AS Roma news from RSS feeds and Italian/English web sources.

TODO:
- Load source list from src/config/sources.yaml
- Fetch RSS feeds using feedparser
- Fetch non-RSS sources via requests + HTML parsing
- Filter items to the given date window
- Deduplicate stories that appear across multiple outlets
- Return a list of normalized item dicts: {headline, summary, source, url, date, category}
"""
