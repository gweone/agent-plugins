# Selectable-text PDF renderer and inline URL

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

## 6. Worked example: selectable-text PDF preview (real, in the original consuming workspace)

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
in the original consuming workspace. Shape:

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
        return null;   // Small card thumbnail stays on the separate stock raster path
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
content" panel simultaneously ([full-content renderer chain](preview-pipeline-and-providers.md)) — one component, no core files touched, thumbnails
untouched.

---

## Reference implementation in the original consuming workspace

`modules/search/src/main/java/org/sharpps/search/contributors/preview/PDFPreviewRendererProvider.java`
— the selectable-text PDF override illustrated above, registered inside the existing
`org.sharpps.search` bundle (no new module).
