Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

## 2. FreeMarker (`.ftl`) macros — Display Templates & Theme Templates

FTL files (display templates under `.../display/template/dependencies/*.ftl`, theme templates
like `portal_normal.ftl`) **cannot** use `<%@ taglib %>` — that's JSP-only syntax. Two different
mechanisms exist instead:

### a) Pre-bound macro namespaces (no import needed)

`clay` and `liferay` are injected as ready-to-use global FTL variables in every display
template — just call them, no `<#import>`/`<#assign>` required:

```ftl
<@clay.icon symbol="trash" />
<@clay.button displayType="secondary" label="Close" data\-action="modalClose" />
<@liferay.language key="my-language-key" />
```

`clay` exposes the same component set as `liferay-clay.tld`: `icon`, `button`, `label`, `link`,
`select`, `badge`, `sticker`, `dropdown-menu`, `dropdown-actions`, `management-toolbar`,
`multiselect`, `navigation-bar`, `navigation-card`, `pagination-bar`, `panel`, `panel-group`,
`progressbar`, `radio`, `checkbox`, `toggle`, `row`, `col`, `container`, `container-fluid`,
`content-row`, `content-col`, `content-section`, `sheet`, `sheet-header`, `sheet-footer`,
`sheet-section`, `tabs`, `tabs-panel`, `user-card`, `vertical-card`, `vertical-nav`,
`horizontal-card`, `file-card`, `image-card`, `alert`. **No `modal` macro** — see [tag verification](../../liferay-jsp-taglibs/references/tag-and-css-verification.md).

`liferay` exposes a small set of theme/i18n helpers: `language`, `language_format`,
`breadcrumbs`, `control_menu`, `navigation_menu`, `search_bar`, `silently`,
`user_personal_bar`.

### b) Generic JSP-taglib bridge: explicit alias, not derived from the `.tld`

FreeMarker has a built-in adapter (`freemarker.ext.jakarta.jsp.TaglibFactory`, wired in
`FreeMarkerManager.java`) that turns a JSP custom taglib into an FTL namespace. **The FTL alias
is not auto-derived from the `.tld`'s `<short-name>`** — don't guess it by replacing hyphens with
underscores; that pattern happens to match for `liferay-aui`→`liferay_aui` but is coincidental.
The real source is a literal `Map<alias, tldPath>` that `FreeMarkerManager`'s bundle tracker
builds by reading one specific file out of *every* bundle: `/META-INF/taglib-mappings.properties`
(see [custom registration](../../liferay-custom-taglib/references/registration-and-composition.md) to register your own taglib for FTL use). Confirmed real
examples (`grep`-able in `liferay-portal`):

| FTL namespace | `taglib-mappings.properties` entry | Example (real, from liferay-portal source) |
|---|---|---|
| `clay` | `clay=/META-INF/liferay-clay.tld` | `<@clay.icon symbol="trash" />` |
| `liferay_aui` | `liferay_aui=/META-INF/liferay-aui.tld` | `<@liferay_aui.script use="liferay-map-base">...</@liferay_aui.script>` |
| `liferay_ui` | `liferay_ui=/META-INF/liferay-ui.tld` | `<@liferay_ui.message key="there-are-no-categories" />`, `<@liferay_ui.panel>`, `<@liferay_ui.icon ... />` |
| `liferay_portlet` | `portlet=/META-INF/liferay-portlet.tld` (note: alias ≠ `liferay_portlet` here — check the file, don't assume) | `<@liferay_portlet.runtime portletName="..." />` |

Note `clay`'s alias is `clay`, not `liferay_clay`, even though its `.tld`'s `<short-name>` is
`liferay-clay` — proof the alias is whatever the `.properties` file says, independent of the
`.tld` itself.

**Use this bridge sparingly.** It works because FreeMarker fakes a JSP page-context for the tag,
but:
- Several bridged tags are **deprecated** (e.g. `aui:fieldset` → `@deprecated As of Cavanaugh
  (7.4.x), with no direct replacement`) — bridging a legacy tag into new FTL code just imports
  the legacy pattern into a newer file.
- Tags with complex `body-content` that call other taglib classes internally (nested
  `MessageTag`, `IconHelpTag`, etc.) assume a normal JSP page lifecycle. Display Templates run
  through `PortletDisplayTemplate`, a different rendering pipeline — it usually works, but it's
  an unusual path for something that's often just static markup.
- If a tag's actual rendered output is simple static HTML (check the tag's Java class — look for
  a `processStartTag()`/`processEndTag()` that just does `jspWriter.write(...)`), it's almost
  always simpler and more robust to write that HTML directly with Clay CSS classes than to
  bridge the tag.

Reach for `liferay_aui`/`liferay_ui`/`liferay_portlet` only when the tag does real logic you'd
otherwise have to reimplement (e.g. `liferay_ui.message` for localization fallback behavior,
`liferay_portlet.runtime` for embedding a portlet) — not for pure layout/markup tags.
