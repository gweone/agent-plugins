# Full preview pipeline, MIME providers and thumbnails

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
        return null;  // Retain the separate stock thumbnail path unless intentionally changing it
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
practical in the original consuming workspace — see [the inline PDF provider example](inline-pdf-preview.md)).

---

## 3. Preview vs. thumbnail — two unrelated mechanisms, don't conflate them

| | Full-content preview | Small grid/list thumbnail |
|---|---|---|
| Triggered from | `<liferay-asset:asset-display>` full_content template, DL's "View File" page | `DLURLHelper.getThumbnailSrc()` / `AssetRenderer.getThumbnailPath()` |
| Mechanism | `DLPreviewRendererProvider` [SPI described here](preview-pipeline-and-providers.md) | Direct raster PNG lookup: `ImageProcessorUtil` → `PDFProcessorUtil.hasImages()` → `VideoProcessorUtil`, in that order |
| Gated by | Whichever provider's own `isSupported()`/`hasImages()` logic | `dl.file.entry.thumbnail.enabled` (default `true`) |
| Extensible how | Register a higher-ranked [`DLPreviewRendererProvider` described here](preview-pipeline-and-providers.md) | **Not extensible this way** — every stock provider's `getThumbnailDLPreviewRenderer` returns `null`; thumbnails never go through this SPI at all |

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
| `DocumentPreviewRendererProvider` (`document-library-preview-document`) | `application/pdf`, `application/x-pdf`, `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-powerpoint`, OOXML (`.docx`/`.xlsx`/`.pptx`), ODF (`.odt`/`.ods`/`.odp`/`.odg`), `text/plain`, `text/css`, `text/html`, `text/x-jsp`, `application/javascript`, `application/rtf`, `application/wordperfect`, `application/x-sh`, StarOffice formats | **PDF only:** no — bundled PDFBox, optionally Ghostscript-accelerated if `gs` is on `PATH`. **Everything else:** yes — see [Office gates](office-and-diagnostics.md) |
| `ImageDLPreviewRendererProvider` (`document-library-preview-image`) | `dl.file.entry.preview.image.mime.types` (bmp/gif/jpeg/png/tiff/…) | No |
| `AudioDLPreviewRendererProvider` (`document-library-preview-audio`) | `dl.file.entry.preview.audio.mime.types` | No |
| `DLVideoDLPreviewRendererProvider` (`document-library-video`) | `dl.file.entry.preview.video.mime.types` | No |

For the document/PDF provider, the stock preview is a flipbook of page-image PNGs, generated
ahead of time by the matching `DLProcessor` (e.g. `PDFPreviewableDLProcessor` for PDF). That's
why PDF preview is an *image*, not selectable text, out of the box — see [the inline PDF provider example](inline-pdf-preview.md).

---

The thumbnail statements describe the inspected stock raster path, not proof that
all possible thumbnail customization techniques are impossible. This preview SPI is
not the stock card-thumbnail extension point.
