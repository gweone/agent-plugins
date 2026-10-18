---
name: liferay-document-preview-extension
description: >
  Extend Document Library full-content previews with ranked MIME-specific DLPreviewRendererProvider OSGi services; diagnose PDF raster previews, inline/download URLs, Office conversion and async DLFileVersionPreview status. Distinguish asset-display full preview from small card thumbnails.
---

# Liferay Document Library preview extension

Use for the full preview on View File or an asset-display/Search view-content
panel, not the small grid/list thumbnail. Evidence comes from an inspected
portal source snapshot and an earlier consuming workspace's `liferay-dev` runtime.

## Workflow

1. Resolve the current consuming workspace, release and source. Identify the
   full-content asset renderer path before proposing an override.
2. Trace `DLFileEntryAssetRenderer` → DL display context → `renderPreview()` →
   `DLPreviewRendererProvider`; the default full-content path is DL-specific.
3. Register a provider for the exact MIME types with a higher
   `service.ranking:Integer` than the competing provider. One service wins per MIME.
4. Use a real OSGi component, not a Client Extension; an existing API-visible
   bundle is sufficient. Verify release API visibility and manifest imports.
5. For a native selectable-text PDF iframe, use `DLURLHelperUtil.getPreviewURL`
   **without `download=true`**; escape the attribute before writing HTML.
6. Return `null` from `getThumbnailDLPreviewRenderer` to retain the inspected
   stock thumbnail path. Do not promise this SPI changes card thumbnails.
7. For non-PDF Office documents, check the separate document-conversion gate,
   reachable LibreOffice/OpenOffice service and `serverEnabled` configuration.
8. Diagnose asynchronous generation using preview status and generated artifacts,
   rather than treating the first no-preview request as a permanent failure.

## Critical constraints

- Full preview and thumbnail are separate paths. Stock thumbnails use direct
  processor/raster lookup; the inspected stock providers return null for thumbnails.
- The stock document/PDF preview is generated page PNGs, not selectable text.
  PDFBox is bundled; Ghostscript acceleration is optional. Office conversion is separate.
- `getDownloadURL(...)` adds `download=true`, forcing attachment disposition;
  it is not the inline iframe URL.
- `DLPreviewRenderer.render` permits IOException, PortalException and
  ServletException, not generic Exception; narrow helper throws clauses.
- Current inspected `StringPool` is `com.liferay.petra.string.StringPool`.
- `DLFileVersionPreview.previewStatus`: 0 success, 1 failure in the cited source.
  A queued first request may legitimately return no generated preview yet.

## Focused references

- [Full-content chain, ranked MIME SPI, dependencies and thumbnail separation](references/preview-pipeline-and-providers.md)
- [Complete native PDF iframe provider and inline URL example](references/inline-pdf-preview.md)
- [Office flags, runtime evidence, exceptions and async diagnostics](references/office-and-diagnostics.md)

`modules/search`, config/store paths and container names are external examples;
resolve actual current locations rather than treating them as plugin-local files.
