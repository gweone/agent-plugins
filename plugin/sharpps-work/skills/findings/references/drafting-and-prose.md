# Gathering evidence and editing prose

## Workflow: Check → Gather → Draft → Edit → Save → Index

1. **Check** — before doing anything else, look for `docs/findings/README.md`. If
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
     [Converting an existing document](template-and-conversion.md#converting-an-existing-document)) before drafting. The point of this skill is to
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
4. **Edit** — before saving, edit the prose directly using this self-contained checklist:
   use clear, concrete wording; remove em dash overuse, forced rule-of-three lists,
   "it's worth noting"-style filler, inflated language, vague attributions, and passive
   voice that hides who found or built what. Edit the prose inside each field; don't
   touch the structure itself (headings, table, labels). That structure makes the doc
   scannable; freeform prose in its place would undo it.
5. **Save** to `docs/findings/<feature-name>.md` in the current workspace (create
   the `findings/` subfolder if it doesn't exist yet; ask for the filename if the
   feature name is ambiguous). Never write it to a scratch/temp directory — this is meant to stay
   in the repo as a record. If the doc contains anything sensitive, check the [Confidential
   information rules](output-index-and-confidentiality.md#confidential-information) *before* saving — a secret pasted into a committed file stays in git
   history even after later edits.
6. **Index** — add or update this doc's row in `docs/findings/README.md` (create
   it, with its explanatory preamble, if this is the first doc). See [Index file](output-index-and-confidentiality.md#index-file) — this is
   what lets a fresh session pick up open work across docs without the user explaining it again.


Preserve headings, metadata tables, Status/Confidentiality values, numbered findings, and field
labels while editing. Replace vague attribution with a named source when known; otherwise mark
uncertainty rather than inventing an actor. Remove filler such as “it is worth noting,” inflated
claims, forced rule-of-three lists, and repeated em dashes. Prefer direct verbs and clear actors
without changing evidence, meaning, or the recorded decision. No external prose-editing skill is
required.
