Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

## 1. JSP taglibs (`.jsp` / `.jspf` files only)

Declared at the top of the file:

```jsp
<%@ taglib uri="http://liferay.com/tld/aui" prefix="aui" %>
<%@ taglib uri="http://liferay.com/tld/ui" prefix="liferay-ui" %>
```

Liferay portlet JSPs almost always get these via `init.jsp`/`init-ext.jsp` includes, so explicit
`<%@ taglib %>` declarations are often already there — check before adding duplicates.

### Core taglibs and what they're for

| Prefix | URI | Source `.tld` | Use for |
|---|---|---|---|
| `aui` | `http://liferay.com/tld/aui` | `util-taglib/src/META-INF/liferay-aui.tld` | Form inputs (`aui:input`, `aui:select`, `aui:button`), `aui:script`, `aui:nav-bar`, workflow status. **Many tags here are deprecated as of 7.4** (e.g. `aui:fieldset` — check the tag's javadoc/`@deprecated` before using). |
| `liferay-ui` | `http://liferay.com/tld/ui` | `util-taglib/src/META-INF/liferay-ui.tld` | `liferay-ui:search-container` (search containers/tables), `liferay-ui:message` (i18n), `liferay-ui:icon`, `liferay-ui:panel`, `liferay-ui:breadcrumb`, `liferay-ui:input-resource`. |
| `liferay-frontend` / `clay` | `http://liferay.com/tld/clay` | `frontend-taglib-clay/.../liferay-clay.tld` | Clay/Lexicon components: `clay:icon`, `clay:button`, `clay:label`, `clay:dropdown-menu`, `clay:management-toolbar`, `clay:select`, `clay:navigation-bar`, `clay:pagination-bar`, etc. **No `clay:modal` tag exists** — Clay's real Modal is a React component (`@clayui/modal`), not a server-side tag. |
| `liferay-util` | `http://liferay.com/tld/util` | `liferay-util.tld` | `liferay-util:include`, `liferay-util:dynamic-include`, `liferay-util:body-top`/`body-bottom`. |
| `theme` | `http://liferay.com/tld/theme` | `liferay-theme.tld` | `theme:defineObjects`, theme-scoped helpers — mostly used in theme templates, not portlet JSPs. |
| `liferay-security` | `http://liferay.com/tld/security` | `liferay-security.tld` | `liferay-security:doAsURL`, permission-check URL helpers. |
| `portlet` | `jakarta.tags.portlet` | `liferay-portlet.tld` / `portlet_4_0` | Standard JSR 362 portlet tags: `portlet:actionURL`, `portlet:renderURL`, `portlet:resourceURL`, `portlet:param`, `portlet:namespace`. |
| `c` | JSTL core | `c.tld` | `c:if`, `c:forEach`, `c:choose` — plain JSTL, not Liferay-specific. |

### Before using a tag

Grep the `.tld` rather than assume the tag/attribute exists or guess its name:

```bash
grep -A 15 "<name>fieldset</name>" "$LIFERAY_PORTAL/util-taglib/src/META-INF/liferay-aui.tld"
```

Check the backing Java class for `@deprecated` — Liferay has quietly deprecated several `aui:`
tags since 7.4 without removing them from the `.tld` (they still "work" but are legacy).

### Gotchas when converting raw HTML to a taglib

These are concrete parse/compile failures hit while replacing hand-written HTML with `aui:`/
`clay:`/`liferay-ui:` tags — not style preferences. See also learn.liferay.com's own taglib
overview: https://learn.liferay.com/w/dxp/development/traditional-java-based-development/developing-a-web-application/using-mvc/tag-libraries

- **A custom tag's attribute value cannot contain a nested custom tag call — only a scriptlet
  or literal text.** `<portlet:namespace/>`, `<liferay-ui:message .../>`, etc. only get parsed
  when they appear in *template text* position (raw HTML, or a JSP's top-level body) — Jasper
  treats a custom tag's attribute value as either a plain string or a single `<%= %>`
  expression, not a place where another tag invocation gets evaluated. Both of these look
  identical to the eye but only the first compiles:

  ```jsp
  <%-- Raw HTML attribute: this works fine --%>
  <input id="<portlet:namespace />foo" />

  <%-- Same pattern on a CUSTOM TAG's attribute: fails --%>
  <clay:button id="<portlet:namespace />foo" />
  <%-- Jasper error: "equal symbol expected", or the literal text
       "<portlet:namespace />foo" gets passed to setId() unparsed and never matches
       anything client-side JS looks up --%>
  ```

  Fix: use a scriptlet expression instead, evaluated entirely in Java:

  ```jsp
  <clay:button id="<%= liferayPortletResponse.getNamespace() + \"foo\" %>" />
  ```

  Same failure mode for embedding one taglib inside another's attribute — e.g.
  `closeButtonAriaLabel="<liferay-ui:message key="remove" />"` on a `<clay:label>` fails the
  same way; use `<%= LanguageUtil.get(request, \"remove\") %>` instead.

- **Quote-escaping depends on *where* the scriptlet lives, and this is the single easiest
  mistake to make when moving between raw HTML and a custom tag.** Inside a **custom tag's**
  attribute value, a `<%= %>` expression is parsed as a nested Java string literal, so any
  literal quotes inside it need `\"` escaping:

  ```jsp
  <clay:label label="<%= HtmlUtil.escape(value) %>" />                          <%-- fine, no literal quotes inside --%>
  <clay:label label="<%= \"hide\".equals(mode) ? \"A\" : \"B\" %>" />           <%-- needs \" --%>
  ```

  Inside **raw HTML** template text (a plain `<div>`, `<input>`, etc. — not a custom tag), the
  same scriptlet must use *plain*, unescaped quotes — the backslash-escaping is invalid Java
  syntax there and breaks the generated servlet with `illegal character: '\'` /
  `unclosed string literal`:

  ```jsp
  <div style="<%= "hide".equals(mode) ? "display:none;" : "" %>">   <%-- correct in raw HTML --%>
  <div style="<%= \"hide\".equals(mode) ? \"display:none;\" : \"\" %>">  <%-- compile error --%>
  ```

  When copy-pasting a scriptlet between a custom-tag attribute and a raw-HTML attribute (a
  common move when converting one to the other), always re-check whether the quotes need
  escaping for the *new* context — don't carry the old context's escaping over.

- **A workspace with `-Werror` on javac turns a deprecated-tag warning into a hard build
  failure.** `<aui:button>` (and several other `aui:` tags) are `@deprecated` as of 7.4 —
  compiling still "works" in isolation, but if the workspace's `compileJSP`/javac config has
  `-Werror`, using one fails the *entire module's* build the moment any file in it triggers a
  deprecation warning. Check `ButtonTag.java`'s javadoc for the replacement
  (`com.liferay.frontend.taglib.clay.servlet.taglib.ButtonTag`, i.e. `<clay:button>`) before
  reaching for the `aui:` version of a tag that also exists under `clay:`.

- **Renaming an element's CSS class to dodge a stock library's auto-wiring can silently break
  an unrelated thing the same class was responsible for.** Interactive elements (e.g. facet
  checkboxes) are sometimes rendered `disabled` by default — a progressive-enhancement
  precaution so a JS failure means "inert," not "broken" — and re-enabled by a stock script's
  own init pass, scoped by CSS class (e.g. Liferay's `FacetUtil` re-enables every `.facet-term`
  checkbox once its JS module loads). If a custom behavior needs to intercept that same
  element's events instead of the stock wiring, changing its class to opt out of the stock
  `onChange` handler *also* opts it out of whatever else keyed off that class — including
  something as easy to overlook as "what turns off `disabled`." Whenever you deliberately give
  an element a distinct class specifically to bypass a library's default handling, audit what
  *else* was keyed off the original class and reimplement it yourself if needed.

- **Non-ASCII characters (em dash, ×, curly quotes, …) written directly into JS source or JS
  comments inside `<aui:script>` can come out mojibake'd** (e.g. `—` becomes `â`, `×` becomes
  `Ã—`), depending on how the `.jsp` file's bytes get re-encoded along the way. This silently
  corrupts anything inside a JS string literal (a rendered `×` button glyph shows garbage) and
  is merely cosmetic-but-ugly inside comments. Always use plain ASCII in JS embedded in a JSP —
  `--` instead of `—`, and a `\uXXXX` escape (`'×'`) instead of a literal Unicode character
  in any JS string that actually renders.

- **`<aui:input type="checkbox">` has two independent attributes, easy to conflate:** `checked`
  (boolean — the initial checked state) and `value` (the string actually submitted when
  checked). A simple on/off preference toggle can get away with only setting `value` to a
  boolean (an existing shortcut some codebases rely on), but the moment you need a *real*
  submitted string alongside independent checked/unchecked state (e.g. one checkbox per option
  in a dynamic list), set both explicitly — don't assume `value` alone drives the visual
  checked state.

- **Find a real precedent before hand-rolling a non-trivial pattern.** For anything beyond a
  single form field — a removable chip/tag list, a picker-driven multi-select, a button that
  only triggers JS — grep `liferay-portal`'s own admin JSPs for the same UI shape before
  inventing markup. E.g. `modules/apps/site/site-admin-web/.../site_settings/
  default_user_associations.jsp` shows the real "item-selector picker → removable list → hidden
  CSV-of-primary-keys input" pattern via `liferay-ui:search-container`, and
  `modules/apps/dynamic-data-mapping/dynamic-data-mapping-web/.../edit_structure.jsp` shows a
  plain `<aui:button onClick="...">` that only opens a picker, never submits a form.
