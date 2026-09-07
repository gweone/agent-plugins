---
name: liferay-document-preview-extension
description: Use whenever the user wants to change, extend, or debug how Liferay renders a Document Library file's full-content preview — the panel/page from the liferay-asset:asset-display tag (Document Library's "View File" page, the Search widget's "view content" result panel, or other asset-display usage), as opposed to the small thumbnail in a grid/list card. Trigger for "PDF preview is an image, can't select text", "extend/override document preview", "DLPreviewRendererProvider", "custom PDF viewer", "why does DOCX/Office preview not work", "OpenOffice/LibreOffice conversion not enabled", "preview vs thumbnail", "service.ranking override for preview", "PDFProcessorUtil", "DLFileVersionPreview status", or any work adding a `@Component(service = DLPreviewRendererProvider.class)`. Confirmed by reading the real `liferay-portal` source and inspecting a live `liferay-dev` container/DB — see the reference implementation in `modules/search`.
---

# Extending Document Library Preview Rendering

## 0. The one-sentence version

**Full-content preview and the small thumbnail are two entirely separate mechanisms** — the
thumbnail is always a raster PNG with no extension point, but the full preview is resolved
through a genuine OSGi whiteboard SPI (`DLPreviewRendererProvider`) that you can outrank with
your own component, for one specific mimetype, without touching or overriding any core file.

---

## 1. The chain from `<liferay-asset:asset-display>` to a preview renderer

For a `FileEntry` asset with the default `full_content` template (`AssetRenderer.TEMPLATE_FULL_CONTENT`
— what `<liferay-asset:asset-display>` uses unless `template="abstract"` is set explicitly),
`DLFileEntryAssetRenderer.getJspPath()` points at a **Document-Library-specific** JSP, not the
generic `asset-taglib` fallback:

```
DLFileEntryAssetRenderer.getJspPath(request, "full_content")
  → "/document_library/asset/file_entry_full_content.jsp"
    → dlDisplayContextProvider.getDLViewFileVersionDisplayContext(request, response, fileVersion)
    → if dlViewFileVersionDisplayContext.hasPreview():
        include "/document_library/view_file_entry_simple_view.jsp"
          → dlViewFileVersionDisplayContext.renderPreview(request, response)
            → dlPreviewRendererProvider.getPreviewDLPreviewRenderer(fileVersion)
                .render(httpServletRequest, httpServletResponse)
```

`dlDisplayContextProvider` is `DLDisplayContextProviderImpl`
(`document-library-web`). Confirmed by reading
`file_entry_full_content.jsp` and `view_file_entry_simple_view.jsp` directly — this is **not** a
generic asset-display code path, it's Document-Library-specific, and it's exactly the same chain
Document Library's own native "View File" page uses. That means one override affects **both**
places automatically — you never need to touch the OOTB Search widget's `view_content.jsp` or any
other `<liferay-asset:asset-display>` caller.

---

## 2. The extension point: a single-value, mimetype-keyed OSGi whiteboard

`DLDisplayContextProviderImpl` tracks every `@Component(service = DLPreviewRendererProvider.class)`
in the system into one map, keyed by mimetype:

```java
_serviceTrackerMap = ServiceTrackerMapFactory.openSingleValueMap(
    bundleContext, DLPreviewRendererProvider.class, null,
    (serviceReference, emitter) -> {
        DLPreviewRendererProvider provider = bundleContext.getService(serviceReference);
        for (String mimeType : provider.getMimeTypes()) {
            emitter.emit(mimeType);
        }
    });
```

`openSingleValueMap` means **exactly one provider wins per mimetype** — ties are broken by OSGi
`service.ranking` (default `0`). Register your own component claiming the same mimetype with a
higher ranking, and Liferay's own lookup (`_serviceTrackerMap.getService(fileVersion.getMimeType())`)
silently prefers yours. No core file is overridden or patched — this is a supported, first-class
extension point, not a hack:

```java
@Component(
    property = "service.ranking:Integer=100",
    service = DLPreviewRendererProvider.class
)
public class MyPreviewRendererProvider implements DLPreviewRendererProvider {

    @Override
    public Set<String> getMimeTypes() {
        return Set.of(ContentTypes.APPLICATION_PDF, ContentTypes.APPLICATION_X_PDF);
    }

    @Override
    public DLPreviewRenderer getPreviewDLPreviewRenderer(FileVersion fileVersion) {
        return (httpServletRequest, httpServletResponse) -> { /* write the response */ };
    }

    @Override
    public DLPreviewRenderer getThumbnailDLPreviewRenderer(FileVersion fileVersion) {
        return null;  // see Section 3 — leave thumbnails alone unless you mean to change them
    }
}
```

**Deployment shape:** `DLPreviewRendererProvider` is a `document-library-api` (portal-kernel SPI)
interface — a Client Extension **cannot** implement it. This must be a real OSGi module. If your
module already has `compileOnly group: "com.liferay.portal", name: "release.dxp.api"` in
`build.gradle` and a `bnd.bnd` with `Import-Package: !com.liferay.*.internal.*, *` (or an explicit
import for `com.liferay.document.library.preview`), no new dependency is needed — the interface is
already visible at compile time and will resolve at runtime against the already-deployed
`com.liferay.document.library.api` bundle. There is no requirement that this live in a
document-library-themed module; any existing bundle can register the component (confirmed
practical in this repo — see Section 6).

---

## 3. Preview vs. thumbnail — two unrelated mechanisms, don't conflate them

| | Full-content preview | Small grid/list thumbnail |
|---|---|---|
| Triggered from | `<liferay-asset:asset-display>` full_content template, DL's "View File" page | `DLURLHelper.getThumbnailSrc()` / `AssetRenderer.getThumbnailPath()` |
| Mechanism | `DLPreviewRendererProvider` SPI (Section 2) | Direct raster PNG lookup: `ImageProcessorUtil` → `PDFProcessorUtil.hasImages()` → `VideoProcessorUtil`, in that order |
| Gated by | Whichever provider's own `isSupported()`/`hasImages()` logic | `dl.file.entry.thumbnail.enabled` (default `true`) |
| Extensible how | Register a higher-ranked `DLPreviewRendererProvider` (Section 2) | **Not extensible this way** — every stock provider's `getThumbnailDLPreviewRenderer` returns `null`; thumbnails never go through this SPI at all |

Confirmed by reading all four stock providers
(`DocumentPreviewRendererProvider`, `ImageDLPreviewRendererProvider`, `AudioDLPreviewRendererProvider`,
`DLVideoDLPreviewRendererProvider`) — none of them implement `getThumbnailDLPreviewRenderer`
beyond returning `null`. **If you only want to change the big preview and leave the small card
thumbnail as-is (the common case), return `null` from `getThumbnailDLPreviewRenderer` in your own
component too** — it's not optional wiring, it's the entire mechanism by which thumbnails stay on
the stock raster-PNG path.

---

## 4. Stock `DLPreviewRendererProvider` coverage

| Provider (module) | Mimetypes | Needs external service? |
|---|---|---|
| `DocumentPreviewRendererProvider` (`document-library-preview-document`) | `application/pdf`, `application/x-pdf`, `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-powerpoint`, OOXML (`.docx`/`.xlsx`/`.pptx`), ODF (`.odt`/`.ods`/`.odp`/`.odg`), `text/plain`, `text/css`, `text/html`, `text/x-jsp`, `application/javascript`, `application/rtf`, `application/wordperfect`, `application/x-sh`, StarOffice formats | **PDF only:** no — bundled PDFBox, optionally Ghostscript-accelerated if `gs` is on `PATH`. **Everything else:** yes — see Section 5 |
| `ImageDLPreviewRendererProvider` (`document-library-preview-image`) | `dl.file.entry.preview.image.mime.types` (bmp/gif/jpeg/png/tiff/…) | No |
| `AudioDLPreviewRendererProvider` (`document-library-preview-audio`) | `dl.file.entry.preview.audio.mime.types` | No |
| `DLVideoDLPreviewRendererProvider` (`document-library-video`) | `dl.file.entry.preview.video.mime.types` | No |

All four render the **same way** for documents/PDF: a flipbook of page-image PNGs, generated
ahead of time by the matching `DLProcessor` (e.g. `PDFPreviewableDLProcessor` for PDF). That's
why PDF preview is an *image*, not selectable text, out of the box — see Section 6.

---

## 5. Office/OOXML/ODF preview needs a second, unrelated feature flag

Unlike PDF (self-contained, PDFBox bundled), DOCX/XLSX/PPTX/ODT/RTF preview requires converting
the file to PDF first via an **external LibreOffice/OpenOffice headless server** — a completely
separate gate from anything in Section 2-4:

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

## 6. Worked example: selectable-text PDF preview (real, in this repo)

Goal: PDF preview shows real, copyable text via the browser's native PDF renderer, instead of
Liferay's raster PDFBox/Ghostscript page-image flipbook — without touching Liferay core.

**Getting the right URL** — do not reuse the *download* URL for the `<iframe src>`. Confirmed by
reading `DLURLHelperImpl`:

```java
getDownloadURL(...) == getPreviewURL(...) + "&download=true"   // forces Content-Disposition: attachment
```

`getPreviewURL(...)` **without** `download=true` is the inline-viewable friendly URL — the one
that lets the browser render the PDF in place instead of downloading it:

```java
String previewURL = DLURLHelperUtil.getPreviewURL(
    fileEntry, fileVersion, themeDisplay, StringPool.BLANK, false, true);
```

**Full component** — reference implementation at
`modules/search/src/main/java/org/sharpps/search/contributors/preview/PDFPreviewRendererProvider.java`
in this repo. Shape:

```java
@Component(
    property = "service.ranking:Integer=100",
    service = DLPreviewRendererProvider.class
)
public class PDFPreviewRendererProvider implements DLPreviewRendererProvider {

    @Override
    public Set<String> getMimeTypes() {
        return _MIME_TYPES;   // application/pdf, application/x-pdf
    }

    @Override
    public DLPreviewRenderer getPreviewDLPreviewRenderer(FileVersion fileVersion) {
        return (httpServletRequest, httpServletResponse) -> _render(
            fileVersion, httpServletRequest, httpServletResponse);
    }

    @Override
    public DLPreviewRenderer getThumbnailDLPreviewRenderer(FileVersion fileVersion) {
        return null;   // Section 3 — small card thumbnail stays the raster image
    }

    private void _render(
            FileVersion fileVersion, HttpServletRequest httpServletRequest,
            HttpServletResponse httpServletResponse)
        throws IOException, PortalException {

        FileEntry fileEntry = fileVersion.getFileEntry();
        ThemeDisplay themeDisplay =
            (ThemeDisplay)httpServletRequest.getAttribute(WebKeys.THEME_DISPLAY);

        String previewURL = DLURLHelperUtil.getPreviewURL(
            fileEntry, fileVersion, themeDisplay, StringPool.BLANK, false, true);

        httpServletResponse.setContentType(ContentTypes.TEXT_HTML);
        httpServletResponse.getWriter().write(
            "<iframe class=\"sharpps-pdf-preview\" src=\"" +
                HtmlUtil.escapeAttribute(previewURL) +
                "\" style=\"border:0;height:75vh;width:100%;\" " +
                "title=\"PDF preview\"></iframe>");
    }
}
```

This affects Document Library's own "View File" page **and** the OOTB Search widget's "view
content" panel simultaneously (Section 1) — one component, no core files touched, thumbnails
untouched.

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
   (Section 2). Splitting it into a new module is a naming/scope judgment call, not a technical
   constraint.

## Reference implementation in this repo

`modules/search/src/main/java/org/sharpps/search/contributors/preview/PDFPreviewRendererProvider.java`
— the selectable-text PDF override from Section 6, registered inside the existing
`org.sharpps.search` bundle (no new module).
