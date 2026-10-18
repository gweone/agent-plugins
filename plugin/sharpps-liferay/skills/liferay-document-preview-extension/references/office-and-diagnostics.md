# Office conversion gates and preview diagnostics

[Skill workflow and reference index](../SKILL.md)

> Evidence scope: retained from source tracing and live debugging in an earlier consuming
> Liferay workspace, not executed or re-verified in this plugin repository. Resolve the
> current workspace, target release and applicable local rules before applying examples.
> `modules/search` (`sharpps-search`), `client-extensions/liferay-global-extension`,
> initializer paths, `.claude/rules/cx.md`/`CLAUDE.md`, `configs/local`, `bundles`, and
> container `liferay-dev` are external workspace examples, not plugin-local files or links.
> Resolve `$LIFERAY_PORTAL` with [liferay-portal-source](../../liferay-portal-source/SKILL.md)
> for source citations; line numbers describe the inspected snapshot, not every release.
> Headings retain original numbering for provenance; navigation uses topical links.

## 5. Office/OOXML/ODF preview needs a second, unrelated feature flag

Unlike PDF (self-contained, PDFBox bundled), DOCX/XLSX/PPTX/ODT/RTF preview requires converting
the file to PDF first via an **external LibreOffice/OpenOffice headless server** — a completely
separate gate from the [ranked preview-provider and thumbnail paths](preview-pipeline-and-providers.md):

```
DocumentPreviewRendererProvider.isSupported(mimeType)
  → (for non-PDF mimetypes) _documentConversion.isEnabled()
    → DocumentConversionImpl.isEnabled()
      → OpenOfficeConfiguration.serverEnabled()   // @Meta.AD deflt = "false"
```

`serverEnabled` **defaults to `false`**, and there's no bundled `soffice` binary in a stock
Liferay container — confirmed by checking a live `liferay-dev` container: no `soffice`/
`libreoffice` binary anywhere on it, no `OpenOfficeConfiguration.config` under `osgi/configs`, no
LibreOffice sidecar container on the Docker network. **If DOCX preview "doesn't work," this is
almost always why** — not a bug, just an unconfigured optional feature.

To enable it: run a LibreOffice/OpenOffice headless server reachable from the portal
(`soffice --headless --accept="socket,host=0.0.0.0,port=8100;urp;"`, typically a sidecar
container), then either flip **Control Panel → System Settings → Connectors → OpenOffice** (Server
Enabled, Server Host, Server Port), or drop a `.config` file for
`com.liferay.document.library.document.conversion.internal.configuration.OpenOfficeConfiguration`
under `configs/local/osgi/configs/`.

---

## 7. Gotchas hit while building this

1. **`DLPreviewRenderer.render(...)`'s functional-interface signature only permits
   `throws IOException, PortalException, ServletException`** — not generic `Exception`. A helper
   method declared `throws Exception` breaks the lambda's target-type match: the IDE/compiler
   reports "Unhandled exception type Exception" at the lambda site, not at the helper's own
   signature. Narrow it to the actual checked exceptions you throw.
2. **`StringPool` moved.** `com.liferay.portal.kernel.util.StringPool` does not exist in current
   Liferay — it's `com.liferay.petra.string.StringPool` (`petra-string` module). Grep the rest of
   your module for the import already in use rather than guessing/assuming the old kernel package.
3. **Async preview generation.** The first time a file is previewed, the backing `DLProcessor`'s
   `hasImages(fileVersion)` (e.g. `PDFPreviewableDLProcessor`) returns `false` immediately and
   fires off async generation (`_queueGeneration`) — the request that triggered it gets no
   preview. A later request, after the background job finishes, will. When something "doesn't
   preview," check real state before guessing:
   - `DLFileVersionPreview` table, `previewStatus` column: `0` = success, `1` = failure
     (`DLFileVersionPreviewConstants`).
   - Generated files on disk:
     `{store}/document_library/{companyId}/0/document_preview/{...}/{fileEntryId}/{fileVersionId}/{page}.png`
     and `.../document_thumbnail/{...}/{fileEntryId}/{fileVersionId}.png`.
4. **Don't assume "new module" is required.** `DLPreviewRendererProvider` is just another
   `@Component` — it can live in any existing bundle that already has API visibility to it
   ([provider API visibility](preview-pipeline-and-providers.md)). Splitting it into a new module is a naming/scope judgment call, not a technical
   constraint.
