"""
Translate Italian content and summarize items via the Anthropic API.

TODO:
- Accept a list of raw item dicts from gather.py
- Detect language of each item (Italian vs. English)
- For Italian items: call Anthropic API to translate + summarize
- For English items: call Anthropic API to summarize only
- Attach reliability flag: confirmed / reported / rumor (inferred from source + language)
- Return enriched item dicts ready for draft.py
"""
