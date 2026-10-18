# Setup, verification, and output location

## Setup

Install only with authorization in the chosen environment (prefer an isolated environment).
The package exposes a cross-platform API but depends on libraries such as `lxml`; availability
of wheels/build dependencies varies by platform. No Word or LibreOffice installation is needed
to generate the file.

```bash
pip install python-docx
```

(Import name is `docx`, package name is `python-docx` — don't confuse it with the unrelated
abandoned `docx` PyPI package.)

## Verification

Always re-open the generated file and sanity-check it before reporting the task done — a
malformed image embed or bad OOXML element can silently produce a file Word refuses to open,
which a script exiting 0 will not reveal:

```python
from docx import Document
d = Document("/path/to/Output.docx")
print("paragraphs:", len(d.paragraphs))
print("tables:", len(d.tables))
print([p.text for p in d.paragraphs if p.style.name.startswith("Heading")])
```

Confirm the heading list matches the intended outline and the paragraph/table counts are
non-trivial (a suspiciously low count usually means a section silently failed to add).

## Where to save

If the document is a real deliverable (not a one-off scratch artifact), save it into the
relevant project's own repo — typically a `docs/` folder — not a temp/scratchpad path, so it's
versioned and discoverable alongside the code/content it documents.

## Structural checks are not visual verification

Reopening with python-docx checks that it can parse the package, not that Word will display
every element correctly. If checking the ZIP, test archive integrity and expected document/media
parts too; neither check proves pagination, image legibility, table fit, or layout quality.

Compare the headings and content against the outline; check embedded image presence and counts,
table content, captions, and output path. When an approved renderer/viewer is available, inspect
the rendered pages for clipped tables, overflow, page breaks, spacing, and readable screenshots.
If visual inspection is unavailable, report that limit explicitly rather than calling the layout
verified. Do not install or launch a viewer without appropriate scope.
