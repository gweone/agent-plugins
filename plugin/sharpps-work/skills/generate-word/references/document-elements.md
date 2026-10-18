# Document elements and formatting examples

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

`width=6.3` inches fits US Letter with one-inch margins, but A4 with those margins has
only about 6.27 inches available. Set width from the actual page width minus margins and
adjust down for a two-column layout; don't rely on python-docx to auto-fit.

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

