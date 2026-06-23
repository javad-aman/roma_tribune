# Weekly Workflow

This is the step-by-step ritual for producing each Roma Tribune issue.

---

## 1. Gather

**When:** Monday or Tuesday, after the weekend's match and news cycle has settled.

1. Open the Claude Project configured with `prompts/project-instructions.md`.
2. Paste or type a gather request specifying the **date window** (e.g., "June 16–22, 2026").
3. Open `content/covered-log.md` and paste the table into the same message so the assistant knows what to skip.
4. The assistant searches Italian and English sources, translates, deduplicates, and returns a digest grouped by: **Transfers**, **Match & Results**, **Club & Other**.
5. Review the digest. Flag anything that looks wrong or needs a second source.

---

## 2. Filter

1. Review the digest against the covered log yourself.
2. Drop any item that is purely a repeat with no new facts.
3. Promote any item marked UPDATE (material new development) to the top of its section.
4. Note which stories you will use — these go into the draft prompt.

---

## 3. Draft

1. Use the gather digest as input to a draft request in the Claude Project (see `prompts/draft.md`).
2. Specify the **opinion angle** for the long-form section (e.g., "tactical breakdown of the match vs. Juventus" or "why the Frattesi sale is a mistake").
3. The assistant returns a full draft: intro, digest, opinion section.
4. Edit the draft into your own voice. Cut anything flat. Sharpen the opinion. Fix any inaccuracies.

---

## 4. Publish

1. Paste the edited draft into Substack. Add any images or formatting.
2. Send or schedule the issue.
3. Update `content/covered-log.md`:
   - Add each story used with today's date and the issue link.
4. Save the final draft as a Markdown file under `content/issues/YYYY-MM-DD-issue-title.md`.

---

## Tools

- **Claude Project** — primary drafting environment (manual phase)
- **Substack** — publication platform
- **`content/covered-log.md`** — prevents story recycling
- **`prompts/`** — instructions and prompt templates for the Claude Project
