Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

Raw HTML props require trusted/sanitized content; parsing HTML is not sanitization.

## 6. Mounting a real React component from a custom taglib

A [custom tag](../../liferay-custom-taglib/SKILL.md) isn't limited to hand-written `jspWriter.write(...)` HTML — it can mount
a real React component client-side, the same mechanism Clay's own tags use (e.g.
`ManagementToolbarTag.getHydratedModuleName()` → `"{ManagementToolbar} from frontend-taglib-clay"`).
This is the right call whenever the tag needs local UI state (dropdown open/close, modals, a fetch
call) that would otherwise mean hand-rolled vanilla JS + `data-action` event delegation.

```java
protected void renderReact(String componentName, Map<String, Object> props)
    throws IOException {

    ComponentDescriptor componentDescriptor = new ComponentDescriptor(
        "{" + componentName + "} from " + _NPM_PACKAGE_NAME,
        getNamespace() + componentName, new LinkedHashSet<>(), false, null);

    _reactRendererSnapshot.get().renderReact(
        componentDescriptor, props, getRequest(), getJspContext().getOut());
}

private static final Snapshot<ReactRenderer> _reactRendererSnapshot =
    new Snapshot<>(BaseTag.class, ReactRenderer.class);
```

- **`ReactRenderer` is genuinely client-side-only.** It writes one empty placeholder `<div>`
  server-side; the component mounts after its JS module loads. There's no SSR — don't reach for
  this for content that must be visible without JS, or that you need server-rendered for SEO.
- **`"{ExportName} from <npm-package-name>"`** resolves to an `index.js`/`index.ts` barrel at your
  module's `META-INF/resources/` root (`<npm-package-name>` = your `package.json`'s `"name"`)
  re-exporting `ExportName` — confirmed by reading `frontend-taglib-clay`'s own `index.js`
  (`export {default as ManagementToolbar} from './management_toolbar/ManagementToolbar';`).
- **`Snapshot<T>`** (`com.liferay.portal.kernel.module.service.Snapshot`, public portal-kernel,
  not Clay-internal) is how a plain `new SomeTag()` instance — JSP/FreeMarker creates these
  directly, they're not Declarative-Services-managed — gets at an OSGi service without
  `@Reference`. Use the same pattern for any other OSGi service your tag needs (e.g. building your
  own helper class that itself needs injected services — construct it with services pulled from
  their own `Snapshot`s, the same way `AssetURLTemplateContextContributor` builds the FTL's
  `assetURLResolver` variable).
- **A string prop containing raw HTML** (e.g. a highlighted-title field with matched-term markup
  the FTL used to emit unescaped via `${...}`) needs `dangerouslySetInnerHTML` on the React side —
  passing it as a body-content vs. an attribute makes no difference once it's serialized into the
  `props` map; either way the component receives a plain string and must choose to render it raw.
  `dangerouslySetInnerHTML` requires a real host element to attach to, though — if the markup
  needs to render with **no wrapper element at all** (e.g. so it sits as a direct child of a flex
  row rather than inside its own `<span>`), that prop has no equivalent on a React `Fragment`.
  Use `html-react-parser` (`parse(htmlString)`) instead — it turns the string into real React
  child nodes you can return/interpolate directly, with no host element required.
- **Resolve page-level state inside the tag, not via FTL-computed parameters.** If something is
  derivable from `RenderRequest`/`ThemeDisplay`/a shared request attribute (current DisplayView,
  active filters, folder-tree state, the portlet namespace), give the tag its own getter for it
  (see the `RenderRequest`/`RenderResponse` retrieval pattern below) instead of having every FTL
  call site recompute and pass it as a parameter. Keep tag attributes limited to values that
  *can't* be reached any other way — typically per-row data tied to the FTL's own loop variable.

### Critical pitfall: every renderReact() call needs its own exclusive parent div

The client-side mount script (`portal-template-react-renderer-impl`'s `render.es.js`) does **not**
mount into the placeholder `<div>` itself:

```js
export default function (renderFunction, renderData, placeholderId) {
    const element = document.getElementById(placeholderId);
    if (element) {
        render(renderFunction, renderData, element.parentElement);
    }
}
```

It mounts into the placeholder's **parent element**. React's `render()`/`createRoot()` takes
ownership of *every child* of that container, not just the placeholder it created — so if two
`renderReact()`-backed tag calls (or a tag call and any other static markup) are direct siblings
under the same parent element, whichever one's script executes first will wipe out everything
else under that shared parent the instant it mounts, including sibling placeholders that haven't
mounted yet and any unrelated static HTML (a table, other markup) that happens to share that
parent. Because script execution order across independent `renderReact()` calls isn't guaranteed,
*which* sibling survives is effectively random from one page load to the next — the symptom looks
like "only one of these three components ever shows, and it's a different one each time" or "this
unrelated block of HTML randomly disappears."

**The fix: wrap every `<@yourtag .../>` call in its own dedicated `<div>`** whenever more than one
such call (or a call alongside other markup) shares an FTL-level parent:

```ftl
<div id="${namespace}wrapper">
    <div><@sharpps["tag-one"] /></div>
    <div><@sharpps["tag-two"] /></div>
    <div class="unrelated-static-markup">...</div>
</div>
```

This is *not* an issue for a `renderReact()` call that's the sole child of its own element already
(e.g. one tag call alone inside a `<td>`) — only when siblings share a parent. Always check this
first when a React-mounted tag's content "disappears" or "only one of several shows" — it's a much
more common cause than a server-side data/logic bug, and the server-rendered HTML (page source)
will look completely correct since this is purely a client-side DOM takeover that happens after
the initial paint.

### Retrieving the live `RenderRequest`/`RenderResponse` from a tag

`PortletRequestImpl`/`PortletResponseImpl` self-register on the underlying `HttpServletRequest`
under `JavaConstants.JAKARTA_PORTLET_REQUEST`/`JAKARTA_PORTLET_RESPONSE` — the exact objects the
FTL's bare `renderRequest`/`renderResponse` variables refer to. This is the same lookup Clay's own
`BaseContainerTag.getNamespace()` uses, just typed differently:

```java
protected RenderRequest getRenderRequest() {
    return (RenderRequest)getRequest().getAttribute(
        JavaConstants.JAKARTA_PORTLET_REQUEST);
}

protected RenderResponse getRenderResponse() {
    return (RenderResponse)getRequest().getAttribute(
        JavaConstants.JAKARTA_PORTLET_RESPONSE);
}
```

This is what lets a tag resolve a shared request attribute (e.g. something a
`PortletSharedSearchContributor` wrote earlier in the same page render) itself, instead of the FTL
reading it and passing it down as a parameter.

### Pitfall: don't share mutable per-call state across a static field

Tag instances are created fresh per render, but a `private static final` field is shared across
*every* concurrent render (different users' requests hitting the same portlet at once).
`java.text.DecimalFormat` (and similarly `SimpleDateFormat`) is mutable and **not thread-safe** —
construct it locally inside the method that uses it, not as a static field, even though it looks
like classic "cache the formatter" boilerplate:

```java
// Wrong — shared mutable state across concurrent renders:
private static final DecimalFormat _decimalFormat = new DecimalFormat("0.#");

// Right — cheap enough to build per call:
private String _formatSize(long bytes) {
    DecimalFormat decimalFormat = new DecimalFormat("0.#");
    ...
}
```
