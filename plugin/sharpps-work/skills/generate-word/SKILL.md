---
name: generate-word
description: Generate genuine Word .docx/OpenXML deliverables with python-docx when users request a Word document, formatted guideline, or manual with headings, tables, screenshots, diagrams, captions, or callouts. Covers document styles, OOXML shading, output placement, structural validation, and separate visual-layout verification.
---

# Generate Word documents with python-docx

Build a real `.docx` programmatically and headlessly, not markdown renamed as Word.
Generation does not require Office or LibreOffice; visual verification is separate.

## Workflow: Spec → Plan → Build → Verify

1. **Spec** — resolve audience, sections, image placement, and the final path.
   Ask when structure or audience is ambiguous. A real deliverable belongs in the
   relevant project's repo, typically `docs/`, not a scratch/temp directory.
2. **Plan** — outline sections and confirm tables/images before generation,
   especially for long documents. Fixing an outline is cheaper than rebuilding.
3. **Prepare** — check for `python-docx` (import `docx`), not the unrelated abandoned
   `docx` package. Install only with authorization in the chosen environment; see
   [setup and verification](references/setup-and-verification.md).
4. **Build** — use [document elements](references/document-elements.md) for the exact
   base styles, title page, screenshot/caption helper, bold table headers, OOXML
   shading, and note/callout helper. Save to the agreed final location.
5. **Verify** — reopen the `.docx`, check outline/content and paragraph/table/image
   presence, then inspect rendered pages when an approved viewer is available.
   Report any missing visual inspection explicitly before handing over the path.

## Formatting rules

- Set base styles once: Calibri 11pt, heading colors, and the examples' brand color
  provide a consistent starting point; adapt them to the requested document design.
- Center screenshot paragraphs and captions; the helper uses italic 9.5pt captions.
  Size images for actual page width/margins; do not assume automatic fitting.
- Use an existing table style and explicitly bold header runs. Raw OOXML is needed
  for cell shading; keep the provided namespace and element handling intact.
- python-docx has no native callout-box element. Use an indented paragraph with a
  bold colored label prefix rather than claiming the helper creates a native box.
- A successful script or readable ZIP/package does not prove correct pagination,
  image legibility, or table layout. Structural checks are necessary, not visual proof.

## Detailed guidance and composition

- [Document elements and formatting](references/document-elements.md) contains all
  runnable construction snippets and reusable helpers, including raw OOXML shading.
- [Setup, verification, and output location](references/setup-and-verification.md)
  contains installation, reopening checks, validation limits, and delivery rules.
- For live images, optionally use [screen-capture](../screen-capture/SKILL.md).
- For an existing findings record, optionally use content from
  [findings](../findings/SKILL.md); map metadata to a
  title-page table and numbered findings to subheadings without redoing the drafting.
