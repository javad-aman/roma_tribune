# Weekly Gather Prompt

<!-- TODO: Weekly gather prompt — to be finalized. -->

## Usage

Paste this prompt into the Claude Project along with:
1. The **date window** for this issue (e.g., "June 16–22, 2026")
2. The contents of `content/covered-log.md` so already-covered stories are skipped

---

## Prompt

<!-- PLACEHOLDER — draft your gather prompt here -->

Gather AS Roma news for the period **[START DATE] to [END DATE]**.

Search Italian sources first (Il Romanista, Corriere dello Sport, Gazzetta dello Sport, Forzaroma.info, ASRoma.com), then English sources (RomaPress, Chiesa Di Totti), then transfer reporters on X (Fabrizio Romano, Gianluca Di Marzio, Angelo Mangiante).

Translate any Italian content into clear English. Deduplicate stories that appear across multiple outlets — cite the most authoritative source.

Already covered (skip unless material new development):

[PASTE COVERED-LOG TABLE HERE]

Return the digest grouped as:
- **Transfers**
- **Match & Results**
- **Club & Other**

Each item: one-line headline, 2–3 sentence summary, source name, publication date, reliability flag (confirmed / reported / rumor).
