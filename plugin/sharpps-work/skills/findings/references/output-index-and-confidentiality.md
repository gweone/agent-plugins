# Output index and confidentiality

## Index file

Docs stay one-per-feature (see [Template](template-and-conversion.md#template)), but `docs/findings/README.md` is
what correlates them — one row per doc, so someone can see every doc's Status and outstanding
count without opening each file. It's a `README.md`, not a bare `index.md`, on purpose: it's the
file a fresh session (agent or human) opens by default on landing in the folder, so the folder
explains its own conventions instead of relying on the user to repeat them or on this SKILL.md
being loaded. Docs themselves stay self-contained and never link to each other — this file is
the only place "what's still open across everything" gets answered.

```markdown
# Findings

Documentation on specific features of this workspace — what was found or built, what was made of
it, and what was decided. One file per feature, following the `findings` skill's
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

- **Doc** links to the actual file (relative path — both live in `docs/findings/`).
- **Outstanding** is the unchecked-item count from that doc's Outstanding section (`0` if the
  section is absent).
- Sort unresolved docs first (`Open`/`Pending`/`Needs decision`, most recent first), `Resolved`
  docs last — the file exists to surface what still needs attention, not as a chronological log.
- Update the row in place when a doc's Status or Outstanding count changes — don't append a new
  row for the same doc, and don't let this file drift out of sync with the doc it points to.
- This file is never `Confidential` — it holds only the non-sensitive feature label/link, date, Status,
  Confidentiality label, and unchecked-item count, never the confidential content itself. If even the feature name is sensitive enough that
  its existence shouldn't appear here, that doc doesn't belong in `docs/findings/`
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
- The `findings/` subfolder doesn't change any of this on its own — namespacing
  keeps this skill's output separate from a project's other documentation, it doesn't make it
  private. Confidentiality still needs its own handling per the rules above regardless of which
  folder the file lands in.

