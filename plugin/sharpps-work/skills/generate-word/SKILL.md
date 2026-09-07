---
name: generate-word
description: Use when the user wants a real Word document — mentions "Word doc", "docx", "OpenXML", "guideline document", "manual", or wants a deliverable that embeds screenshots/diagrams with formatted headings, tables, and captions rather than plain markdown. Covers generating genuine .docx files programmatically via python-docx (no Word/LibreOffice install needed, works headless), including title pages, styled headings, tables with a bold header row, embedded images with captions, note/callout paragraphs (no native callout element in python-docx — built from a bold colored label prefix), and verifying the output isn't corrupted before handing it over.
---

# Generating Word (.docx) documents with python-docx

A real OpenXML document, not markdown-exported-to-Word — built programmatically, headless, no
Office/LibreOffice install required.

**Cross-platform**: `python-docx` is pure Python manipulating XML inside a zip archive — no
native/OS-specific dependencies at all. `pip install python-docx` and every example below work
identically on Windows, macOS, and Linux; nothing in this skill is platform-specific.

## Workflow: Spec → Plan → Build

1. **Spec** — resolve the document's actual structure before writing any code: sections/headings,
   which images go where (if any — pair with the `screen-capture` skill when the images are live
   screenshots, not pre-supplied), and where the finished file should be saved (a real deliverable
   belongs in the relevant repo, e.g. a `docs/` folder — not left in a scratch/temp directory).
   Ask the user if the structure or intended audience is ambiguous.
2. **Plan** — outline the section list and confirm any tables/images to embed before generating,
   especially for a long document — cheaper to fix the outline than to regenerate a 20-page file.
3. **Build** — write and run the generation script, then verify the output (see Verification)
   before reporting it done.

## Setup

```bash
pip install python-docx
```

(Import name is `docx`, package name is `python-docx` — don't confuse it with the unrelated
abandoned `docx` PyPI package.)

## Base structure

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Base styles - set once, applies throughout
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)

BRAND_COLOR = RGBColor(0x1B, 0x4F, 0x8C)
for i in range(1, 4):
    doc.styles[f"Heading {i}"].font.color.rgb = BRAND_COLOR

doc.add_heading("Section Title", level=1)
doc.add_paragraph("Body text.")
doc.add_paragraph("Bullet item", style="List Bullet")

doc.save("/path/to/repo/docs/Output.docx")
```

## Title page

```python
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("Document Title")
run.font.size = Pt(28)
run.bold = True
run.font.color.rgb = BRAND_COLOR

doc.add_page_break()   # before the real content starts
```

## Embedding screenshots with captions

```python
def add_screenshot(doc, path, caption, width=6.3):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(width))

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run(caption)
    cap_run.italic = True
    cap_run.font.size = Pt(9.5)
    cap_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
```

`width=6.3` inches fits a standard US Letter/A4 page with normal margins without overflowing —
adjust down for a two-column layout, don't rely on python-docx to auto-fit.

## Tables

```python
tbl = doc.add_table(rows=1, cols=2)
tbl.style = "Light Grid Accent 1"   # built-in style name - must exist in Word's style gallery
hdr = tbl.rows[0].cells
hdr[0].text = "Column A"
hdr[1].text = "Column B"
for cell in hdr:
    for run in cell.paragraphs[0].runs:
        run.bold = True   # header text isn't bold by default even with a styled table

for a, b in data_rows:
    row = tbl.add_row().cells
    row[0].text = a
    row[1].text = b
```

Cell background shading has no high-level API — needs raw OOXML if truly required:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)
```

## Note/callout paragraphs

python-docx has no native callout-box element — approximate one with a bold colored label:

```python
def add_note(doc, text, label="Note"):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    run = p.add_run(f"{label}: ")
    run.bold = True
    run.font.color.rgb = BRAND_COLOR
    p.add_run(text)
```

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
