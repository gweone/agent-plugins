# Template, conversion, and status

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
  one `findings` doc per entry, each following the normal template, all listed in
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

## Notes

- Keep each field to a sentence or two. This is scannable, not documentation for an external
  audience — if a field runs long, that's a sign it's actually two findings, not one.
- Number findings in the order they matter, not the order they were discovered, if those differ.
- A one-finding doc still uses the numbered-subsection structure (`### 1. ...`) — don't
  special-case it down to flat prose, since the next finding added later should slot in the same
  way.
- If the user later wants this turned into a shareable deliverable, optionally pair with [generate-word](../../generate-word/SKILL.md) to build a `.docx` from the same content — the metadata block maps to a title-page table,
  each numbered finding to its own subheading, don't duplicate the drafting work.
