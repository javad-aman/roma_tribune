# Roma Tribune

An independent, English-language newsletter about AS Roma, published on Substack. Written for the English-speaking diaspora fan who wants real coverage — not wire copy — with a personal, opinionated voice and curated intelligence translated from Italian sources.

## Directory Map

```
roma-tribune/
├── docs/           # Mission, workflow, and source documentation
├── prompts/        # Claude Project instructions and weekly prompts
├── content/
│   ├── issues/     # Published and draft issue files
│   └── covered-log.md  # Running log of stories already covered
├── src/            # Future automation skeleton (stubs only)
│   └── config/
│       └── sources.yaml
└── data/           # Gitignored scratch space for raw pulls and drafts
```

## Weekly Workflow

**Gather** — Search Italian and English sources for AS Roma news published in the current week's date window. Translate Italian articles into English. Deduplicate stories that appear across multiple outlets.

**Filter** — Keep only items within the date window. Cross-reference the `content/covered-log.md` to skip stories already covered unless there is a material new development (fee agreed, medical, deal done/dead, official announcement).

**Draft** — Use the Claude Project (see `prompts/`) to generate a newsletter issue: a short intro, the news digest grouped by category, and one opinion or match-review section. Edit the draft into the owner's voice before publishing.

**Publish** — Paste the edited draft into Substack, update `covered-log.md` with the stories used, and archive the issue file under `content/issues/`.

See `docs/workflow.md` for the full step-by-step ritual.
