---
name: findings
description: Write or convert workspace feature records into numbered Findings, Feedback, and Conclusion with Summary, Status, Confidentiality, and unresolved-item tracking. Use for “document what you found,” “write up findings,” “document this feature,” or restructuring existing notes; saves one Markdown record per topic and maintains docs/findings/README.md as the generated output index.
---

# Findings / Feedback / Conclusion

Create a durable, scannable workspace record of what was found, built, or decided.
This is one feature per Markdown file, not a polished external deliverable.

## Workflow: Check → Gather → Draft → Edit → Save → Index

1. **Check** — read `docs/findings/README.md` first if it exists,
   every time. Reuse the feature's existing doc and follow naming/Status conventions.
2. **Gather** — use evidence already obtained in this session without rerunning it.
   For a supplied source file, read its actual content before converting; a link to
   the original is not a conversion. Split multi-topic sources into one doc per topic;
   ask when topic boundaries are unclear.
3. **Draft** — use the [template and conversion rules](references/template-and-conversion.md).
   Findings are facts with confidence; Feedback is judgment/impact; Conclusion is a
   decision or next step, not a summary of the previous sections.
4. **Edit** — apply the self-contained [prose checklist](references/drafting-and-prose.md).
   Use clear wording; remove filler, inflated language, vague attribution, and em dash
   overuse. Preserve evidence, headings, metadata table, labels, and Status values.
   No external prose-editing skill is required.
5. **Save** — write `docs/findings/<feature-name>.md` in the current
   workspace, never a scratch path. Ask about ambiguous filenames. Check the
   [confidentiality rules](references/output-index-and-confidentiality.md#confidential-information)
   before writing sensitive material; namespacing is not access control.
6. **Index** — create or update the generated
   `docs/findings/README.md` with its explanatory preamble and one
   row per doc. Follow [index rules and template](references/output-index-and-confidentiality.md#index-file).
   This workspace output index is required, not a plugin-wide skill index.

## Invariants

- Keep fields to a sentence or two; split distinct findings and number them by
  importance. Even one finding uses `### 1. ...`; Feedback refers to finding numbers.
- Track small, actionable unchecked items in Outstanding. When all close, set Status
  to `Resolved` and remove Outstanding; synchronize the index row in place.
- Never include actual secrets, credentials, tokens, or full PII. Redact values and
  cite their location. Confirm sensitive findings and destination with the user before
  saving; do not assume repo visibility or silently commit anything.
- Docs remain self-contained and never link to one another. The generated README
  correlates their statuses/counts and must not expose confidential feature content.

## Detailed guidance and composition

- [Gathering and prose editing](references/drafting-and-prose.md): full drafting workflow.
- [Template, conversion, and status](references/template-and-conversion.md): exact record format.
- [Output index and confidentiality](references/output-index-and-confidentiality.md): README and privacy rules.
- Optionally turn the same content into a shareable `.docx` with
  [generate-word](../generate-word/SKILL.md); do not duplicate the drafting work.
