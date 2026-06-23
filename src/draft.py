"""
Assemble a newsletter issue draft from summarized items.

TODO:
- Accept enriched item dicts from summarize.py and an opinion angle string
- Load issue template from content/issues/_template.md
- Call Anthropic API with the gather digest + opinion angle to produce a full draft
- Write the draft to data/ as a dated Markdown file
- Print the output path so the owner can open and edit it
"""
