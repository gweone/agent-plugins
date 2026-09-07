---
name: structured-documentation
description: Use when the user wants a written doc on a workspace feature captured for later — what was found investigating it, what was built/decided, OR an existing doc converted/restructured into this format. Triggers on "document what you found", "write up the findings", "document this feature", "convert this doc to structured-documentation", or after investigating/building/reviewing a feature when the user wants it captured, not just stated in chat. When the source is an existing file, read it and rewrite into the template. A large document covering many topics becomes multiple docs, one per topic. Check docs/structured-documentation/README.md first if it exists, to avoid duplicating a doc and pick up conventions. Covers three distinct sections (facts vs. judgment vs. decision), tracking unresolved items via a Status field, handling confidential content (redact, flag Confidentiality), and a humanizing pass before saving.
---

# Structured documentation: Findings / Feedback / Conclusion

A short, categorized write-up on one feature of the current workspace — not a polished
deliverable, just a durable record of what's there (found, built, or decided), what was made of
it, and what happens next. "Findings" here isn't limited to things discovered by searching — it
covers whatever the section is about, including work the user built or a decision that was made.
Saved as markdown under `docs/structured-documentation/` in the workspace, so it shows up in
`git log`/`git blame` like any other file.

`docs/` is often shared with unrelated project documentation, so this skill namespaces
everything it writes under its own `docs/structured-documentation/` subfolder rather than
dropping loose files straight into `docs/` — that keeps it easy to find, easy to `.gitignore` or
relocate as a unit, and impossible to confuse with a project's other documentation.

## Workflow: Check → Gather → Draft → Humanize → Save → Index

1. **Check** — before doing anything else, look for `docs/structured-documentation/README.md`. If
   it exists, read it first: it lists every existing doc with Status/Outstanding, so it tells you
   whether this feature already has a doc (update that doc instead of creating a duplicate) and
   shows the conventions in use (naming, Status values) without the user having to repeat them.
   This applies every time this skill runs, not just on a brand-new workspace — a fresh session
   has no memory of docs written earlier, the README is how it recovers that context.
2. **Gather** — the source is either of two things:
   - **This conversation** — an investigation via the Explore agent or `codebase-memory-mcp`,
     grep, manual reading, or work the user just built. Don't re-run something that already
     produced an answer earlier in the session.
   - **An existing document the user points at** — a README, a research log, old notes, anything
     already written. Read the file in full (or the relevant part of it, for a large file — see
     Converting an existing document below) before drafting. The point of this skill is to
     restructure real content into the template, not to summarize the file's existence or link to
     it; if the draft doesn't contain the actual substance from the source file, the conversion
     didn't happen.
3. **Draft** the three sections, in order, and keep each one doing a different job — the most
   common failure is letting them blur together:
   - **Findings** — what's actually there: file paths, behavior, root cause, or what was built.
     Facts only, no opinions or recommendations yet.
   - **Feedback** — the reaction to those findings: severity, impact, a reviewer's or the user's
     take. This is where judgment enters.
   - **Conclusion** — the resulting decision or next step, in a sentence or two. Not a
     restatement of Findings or Feedback — if it reads like a summary of the sections above it,
     rewrite it as an actual decision.
4. **Humanize** — before saving, run the draft through the `humanizer` skill to strip AI-writing
   tells: em dash overuse, rule-of-three lists, "it's worth noting"-style filler, inflated
   language, vague attributions, passive voice that hides who found or built what. Humanize the
   prose inside each field — don't touch the structure itself (headings, table, labels); that
   structure is what makes the doc scannable, and freeform "humanized" prose there would undo it.
5. **Save** to `docs/structured-documentation/<feature-name>.md` in the current workspace (create
   the `structured-documentation/` subfolder if it doesn't exist yet; ask for the filename if the
   feature name is ambiguous). Never write it to a scratch/temp directory — this is meant to stay
   in the repo as a record. If the doc contains anything sensitive, check the Confidential
   information rules below *before* saving — a secret pasted into a committed file stays in git
   history even after later edits.
6. **Index** — add or update this doc's row in `docs/structured-documentation/README.md` (create
   it, with its explanatory preamble, if this is the first doc). See Index file below — this is
   what lets a fresh session pick up open work across docs without the user explaining it again.

## Template

The structure exists so a reader can jump straight to the part they need — the metadata block
tells them at a glance whether this is still relevant, the summary is the 10-second version, and
each finding gets its own heading (so it shows up in a markdown outline / VS Code's Outline
panel, and can be linked to directly). Don't collapse the numbered findings back into one prose
paragraph — the numbering is what lets Feedback and Conclusion refer back to a specific finding
instead of vaguely to "the issues above."

```markdown
# <Feature> — Doc

| | |
|---|---|
| **Date** | YYYY-MM-DD |
| **Status** | Open / Pending / Needs decision / Resolved |
| **Confidentiality** | Public / Internal / Confidential |

## Summary
One or two sentences — the takeaway, for a reader who won't read past this line.

## Findings

### 1. <short title>
- **Observed:** what's actually there — concrete, file:line where useful; what was found, or
  what was built
- **Confidence:** Verified / Uncertain — say so if it wasn't directly confirmed

### 2. <short title>
- **Observed:** ...
- **Confidence:** ...

(one subsection per distinct finding — split unrelated observations rather than merging them)

## Feedback
- **On #1:** severity / impact / reviewer's take
- **On #2:** ...

## Conclusion
- **Decision:** the actual call made
- **Next steps:** what happens next, if anything — omit this line if there's nothing pending

## Outstanding
- [ ] item still unresolved — reference the finding number it relates to
- [ ] ...

(omit this section entirely once nothing is left open — don't leave an empty checklist sitting
in a "Resolved" doc)
```

## Converting an existing document

When the source is a file the user already has, not a fresh investigation, two cases:

- **The file covers one feature/topic.** Read it fully, then draft normally: pull its actual
  claims into numbered Findings, its judgment calls into Feedback, its decision into Conclusion.
  Drop anything that was pure narration of the writing process itself (changelogs of the doc, not
  of the feature) — the template captures the feature, not the history of the file about it.
- **The file covers many topics/entries** (a running log, a multi-section wiki page, a journal).
  Do not force it into one doc — that either balloons every field past "a sentence or two" or
  guts most of the content to fit. Instead, treat each distinct topic/entry as its own feature:
  one `structured-documentation` doc per entry, each following the normal template, all listed in
  the shared README.md. A single source file can produce many output docs; that's expected, not
  a sign something went wrong. If it's unclear where one entry ends and the next begins, ask the
  user rather than guessing a split.
- Either way, converting is not linking. Producing a doc whose Findings section just says "see
  `original-file.md` for details" isn't a conversion — it's a pointer, and it defeats the reason
  the user asked for this in the first place (a scannable structure instead of a large file to
  read from scratch).

## Status and Outstanding items

- **Status** in the metadata table is the doc's overall state at a glance: `Open` (still being
  worked on), `Pending` (done, waiting on someone/something external — a decision, a fix, a third
  party), `Needs decision` (ready for a call but nobody's made it yet), `Resolved` (done, kept
  only as a record).
- The **Outstanding** section is where `Pending`/`Needs decision` becomes concrete: a checklist,
  not prose, so it can be ticked off in place as items close instead of rewritten. Each item
  should be small enough to be unambiguously done or not — "decide on X" rather than "sort out the
  X situation."
- When every item in Outstanding is checked, flip Status to `Resolved` and delete the section
  rather than leaving a fully-checked list behind — an all-checked checklist reads as "was
  outstanding," which is stale information a reader has to double-check against Status anyway.

## Index file

Docs stay one-per-feature (see Template above), but `docs/structured-documentation/README.md` is
what correlates them — one row per doc, so someone can see every doc's Status and outstanding
count without opening each file. It's a `README.md`, not a bare `index.md`, on purpose: it's the
file a fresh session (agent or human) opens by default on landing in the folder, so the folder
explains its own conventions instead of relying on the user to repeat them or on this SKILL.md
being loaded. Docs themselves stay self-contained and never link to each other — this file is
the only place "what's still open across everything" gets answered.

```markdown
# Structured Documentation

Documentation on specific features of this workspace — what was found or built, what was made of
it, and what was decided. One file per feature, following the `structured-documentation` skill's
Findings / Feedback / Conclusion structure. Numbered findings within a doc are cross-referenced
by Feedback and Conclusion (`On #1: ...`).

**Status:** `Open` (still in progress) · `Pending` (done, waiting on something external) ·
`Needs decision` (ready for a call) · `Resolved` (closed, kept as a record).
**Confidentiality:** `Public` / `Internal` / `Confidential` — see the doc itself for what that
implies; never a substitute for redacting actual secrets from the doc text.

| Doc | Date | Status | Confidentiality | Outstanding |
|---|---|---|---|---|
| [<Feature>](<feature-name>.md) | YYYY-MM-DD | Pending | Internal | 2 |
| [<Feature>](<feature-name>.md) | YYYY-MM-DD | Resolved | Public | 0 |
```

- **Doc** links to the actual file (relative path — both live in `docs/structured-documentation/`).
- **Outstanding** is the unchecked-item count from that doc's Outstanding section (`0` if the
  section is absent).
- Sort unresolved docs first (`Open`/`Pending`/`Needs decision`, most recent first), `Resolved`
  docs last — the file exists to surface what still needs attention, not as a chronological log.
- Update the row in place when a doc's Status or Outstanding count changes — don't append a new
  row for the same doc, and don't let this file drift out of sync with the doc it points to.
- This file is never `Confidential` — it only ever holds a feature name, a date, and a status
  word, never the confidential content itself. If even the feature name is sensitive enough that
  its existence shouldn't appear here, that doc doesn't belong in `docs/structured-documentation/`
  at all — stop and ask the user where it should go instead.

## Confidential information

Docs are written to a markdown file that lands in `git log`/`git blame` — anything typed into it
is effectively permanent, even if a later commit edits it out. Treat that as the constraint, not
an afterthought at save time:

- **Never paste an actual secret, credential, token, or full PII value into the doc.** Describe
  that it exists and where (`API key hardcoded at config.py:42`), not the value itself. If the
  value must be shown for the finding to make sense, redact it (`sk-***`, last 4 chars only)
  rather than writing it in full.
- Set **Confidentiality** in the metadata table honestly: `Confidential` for anything that
  shouldn't be read outside the immediate team (security vulnerability details, unredacted
  personal data references, internal-only architecture); `Internal` for normal engineering
  detail; `Public` only if the repo itself is public or the content is fine externally.
- If a finding is inherently sensitive (a live vulnerability, exposed credentials, customer PII),
  stop and confirm with the user before saving — don't silently commit a `Confidential` doc to a
  repo that might be shared or public. Ask, don't assume the repo's visibility.
- If the workspace's `docs/` folder is not appropriate for confidential content at all (public
  repo, shared with people outside the need-to-know group), say so and ask where it should go
  instead, rather than saving there by default.
- The `structured-documentation/` subfolder doesn't change any of this on its own — namespacing
  keeps this skill's output separate from a project's other documentation, it doesn't make it
  private. Confidentiality still needs its own handling per the rules above regardless of which
  folder the file lands in.

## Notes

- Keep each field to a sentence or two. This is scannable, not documentation for an external
  audience — if a field runs long, that's a sign it's actually two findings, not one.
- Number findings in the order they matter, not the order they were discovered, if those differ.
- A one-finding doc still uses the numbered-subsection structure (`### 1. ...`) — don't
  special-case it down to flat prose, since the next finding added later should slot in the same
  way.
- If the user later wants this turned into a shareable deliverable, pair with the `generate-word`
  skill to build a `.docx` from the same content — the metadata block maps to a title-page table,
  each numbered finding to its own subheading, don't duplicate the drafting work.
