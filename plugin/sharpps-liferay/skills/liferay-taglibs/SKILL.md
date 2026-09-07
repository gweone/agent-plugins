---
name: liferay-taglibs
description: Use whenever the user asks about Liferay JSP taglibs or FreeMarker (FTL) macros — which tag library to use, how to declare/import one, what tags/macros are available, the difference between a taglib in a JSP vs. an FTL display template, or how to verify a tag/macro exists before using it. Also covers building a custom JSP/FTL taglib from scratch (registration for JSP vs. FTL, sharing logic across separate Portlet Display Template script-files, mounting a React component from a tag, resolving page-level state from RenderRequest instead of FTL parameters, and reflection for calling methods on FTL loop variables whose concrete type is in a non-exported internal package). Trigger for "what taglib has X", "how do I use aui, liferay-ui, or clay tags in this file", "is there an FTL equivalent of tag", "can I use (@liferay_xxx.yyy) here", "how do I share logic between display template files", "how do I make a tag that renders a React component", or any work inside a `.jsp`/`.jspf`/`.ftl` file.
---

# Liferay Taglibs Skill (JSP + FTL)

> Commands below reference `$LIFERAY_PORTAL`, the dynamically-resolved Liferay Portal source
> checkout — see the `liferay-portal-source` skill to resolve/bootstrap it before running them.

Liferay has two separate-but-overlapping tag systems. Knowing which one a file can use, and
which prefix/namespace maps to which library, avoids guessing tag names or inventing markup
that doesn't exist.

> **Important — prefer the taglib/macro over hand-written HTML.** If a `clay:`/`@clay.`,
> `liferay-ui:`/`@liferay_ui.`, or `aui:`/`@liferay_aui.` tag already covers what you're
> building (a button, icon, dropdown, panel, search container, form input...), use it instead
> of writing the equivalent raw `<button>`/`<div>`/`<svg>` by hand. The taglib version stays in
> sync with the theme's design tokens, gets accessibility attributes for free, and won't drift
> when Clay's markup/CSS changes underneath it. Only fall back to plain HTML when no taglib or
> FTL macro actually covers the case (verify with Section 3 below before concluding that) — e.g.
> there's no `clay:modal`/`<@clay.modal>`, so a modal legitimately needs hand-written HTML
> against Clay's own CSS classes.

---

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

---

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
`horizontal-card`, `file-card`, `image-card`, `alert`. **No `modal` macro** — see note above.

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
(see Section 4 — this is also how you register your *own* taglib for FTL use). Confirmed real
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

---

## 3. Verifying before using

Don't guess a tag, macro, or CSS class exists — verify it:

```bash
# Does this JSP tag exist, and what attributes does it take?
grep -A 20 "<name>TAGNAME</name>" "$LIFERAY_PORTAL"/util-taglib/src/META-INF/liferay-*.tld

# Is this tag deprecated? Check its backing class.
find "$LIFERAY_PORTAL" -iname "*TagNameTag.java" -path "*aui*"

# Does this Clay FTL macro exist?
grep -n "<name>" "$LIFERAY_PORTAL/modules/apps/frontend-taglib/frontend-taglib-clay/src/main/resources/META-INF/liferay-clay.tld"

# Does the THEME actually ship the CSS class you're about to rely on?
# (Pull the live compiled clay.css and grep it — don't assume a class exists just
# because it's a "standard" Bootstrap/Clay name.)
curl -s "https://<host>/o/<theme-id>/css/clay.(<hash>).css" -o /tmp/clay.css
grep -o '\.classname{[^}]*}' /tmp/clay.css
```

This last technique — fetching the live theme's compiled CSS — is the most reliable way to
confirm a class/utility actually exists with the values you expect, rather than assuming the
SCSS source in `liferay-portal` matches what's deployed (theme overrides, build-time variable
maps, and Atlas/Cadmin variants can change the compiled output).

### Known Clay CSS gotchas (confirmed via live `clay.css`, not SCSS source)

- **`.label-item{display:flex;flex-direction:column}`** — a Clay label's inner content wrapper
  (the element you pass `innerElementProps`/`className` into on `Toolbar.Label`/`ClayLabel`)
  defaults to a *column* flex direction. Bootstrap's `d-inline-flex` only sets `display`, not
  `flex-direction`, so adding it alone still leaves icon+text stacked vertically — you also need
  `flex-row` explicitly.
- **`.dropdown-item-indicator-start{position:absolute}`** — a `ClayDropDown.Item`'s left-side
  icon/symbol is absolutely positioned and needs its *ancestor* dropdown menu to carry
  `.dropdown-menu-indicator-start` for the padding compensation that keeps it from overlapping
  the label text. `ClayDropDownWithItems` applies that ancestor class automatically; the
  lower-level `ClayDropDown` composition (menu built by hand from `ClayDropDown.Item`s) does not
  — pass `hasLeftSymbols` to `ClayDropDown` to get it, rather than trying to add the class
  manually (it has to land on the right ancestor, not the item itself).

---

## 4. Creating a custom JSP taglib

Custom taglibs are an OSGi-module/JSP concern — Client Extensions have no JSP rendering model,
so this is one of the legitimate cases where a traditional module is the right tool even on
7.4+/Quarterly Release workspaces.

1. **Tag handler class** — extend `jakarta.servlet.jsp.tagext.SimpleTagSupport` (no body
   re-evaluation needed) or `TagSupport` (if you need `doStartTag`/`doEndTag` control), under
   `src/main/java` of the module:

   ```java
   public class MyTag extends SimpleTagSupport {

       public void setLabel(String label) {
           _label = label;
       }

       @Override
       public void doTag() throws JspException, IOException {
           getJspContext().getOut().write("<span class=\"my-tag\">" + _label + "</span>");
       }

       private String _label;
   }
   ```

2. **`.tld` descriptor** — under `src/main/resources/META-INF/my-taglib.tld`:

   ```xml
   <taglib xmlns="https://jakarta.ee/xml/ns/jakartaee" version="3.0">
       <short-name>my</short-name>
       <uri>http://example.com/tld/my</uri>
       <tag>
           <name>thing</name>
           <tag-class>com.example.taglib.MyTag</tag-class>
           <body-content>empty</body-content>
           <attribute>
               <name>label</name>
               <required>true</required>
               <rtexprvalue>true</rtexprvalue>
           </attribute>
       </tag>
   </taglib>
   ```

3. **Use it** in a JSP within the same module (or any module with a build dependency on it +
   the class package `Import-Package`d via `bnd.bnd`):

   ```jsp
   <%@ taglib uri="http://example.com/tld/my" prefix="my" %>
   <my:thing label="Hello" />
   ```

Keep custom taglibs scoped to one module unless there's a clear, concrete need to share across
modules — cross-module taglib sharing means managing `Export-Package`/`Import-Package` in
`bnd.bnd` for the tag classes, which is extra OSGi wiring most single-purpose tags don't need.

### Making the same taglib usable from FTL too

JSP `<%@ taglib %>` resolution and FTL's `<@alias.tag>` resolution are **two independent
registrations** — doing one does not give you the other, and both are easy to half-do without
noticing (the symptom for the missing one is an FTL error: `The following has evaluated to null
or missing: ==> alias`, pointing at your `<@alias...>` call).

1. **JSP-side**: add a `Provide-Capability` header to `bnd.bnd` so the portal's `jsp.taglib`
   OSGi extender picks up your `.tld` (same header `frontend-taglib-clay`/`util-taglib` use):

   ```
   Provide-Capability:\
       osgi.extender;\
           osgi.extender="jsp.taglib";\
           uri="http://example.com/tld/my";\
           version:Version="${Bundle-Version}"
   ```

2. **FTL-side**: add `src/main/resources/META-INF/taglib-mappings.properties` — this is the
   *only* thing that makes `FreeMarkerManager` expose your taglib as a global FTL variable
   (confirmed by reading its `TaglibBundleTrackerCustomizer.addingBundle()` — it looks for this
   exact file path in every bundle; the OSGi capability above is irrelevant to it):

   ```properties
   my=/META-INF/my-taglib.tld
   ```

   The key is your chosen FTL alias; the value is the `.tld`'s path *within this bundle* (not a
   URI). After this, `<@my.thing label="Hello" />` works in any FTL display template, the same
   way `<@clay...>`/`<@liferay_aui...>` do — resolved by registration, not by file path, so it
   works from *any* Display Template/DDMTemplate regardless of which `.ftl` calls it (unlike
   `<#import>`, which fails across separate Portlet Display Template script-files — see the
   warning in Section 2).

Both steps need the module to actually (re)start for the bundle tracker to pick up a brand-new
`.tld`/mapping — a hot-swapped JAR usually still triggers this, but if `<@alias...>` still comes
back null/missing after redeploying, check the bundle actually restarted (not just had its JAR
overwritten in place).

### Reusing another taglib's Java tag class directly (not JSP-include)

If your tag needs to render something another taglib already provides (e.g. you want your
custom tag's output to include real `clay:icon`/`clay:button` markup, not a hand-copied
reproduction of it), the Liferay-idiomatic move for an **OSGi module's own tag** is to drive the
other tag's Java class directly — not `pageContext.include("/some.jsp")`. `include()` resolves
its path against the *current request's* context root, which during a portlet/Display Template
render is the portal ROOT context, not your module's own `Web-ContextPath` — so an include
pointing at your own module's JSP will not resolve. (This is different from legacy taglibs like
`aui:fieldset`, whose `start.jsp`/`end.jsp` ship directly into the portal root webapp's docroot —
not how an OSGi module's own resources are served.)

Instead, since the tag class you want to reuse (e.g. `com.liferay.frontend.taglib.clay.servlet.
taglib.IconTag`) is on your compile classpath (check it's in `release.dxp.api`'s jar or add an
explicit `compileOnly` dependency), drive its standard `TagSupport` lifecycle directly against
your own `PageContext` — its output lands in the exact same `JspWriter` your tag is already
writing to:

```java
protected void writeIcon(String symbol) throws Exception {
    IconTag iconTag = new IconTag();

    iconTag.setPageContext((PageContext)getJspContext());
    iconTag.setSymbol(symbol);

    iconTag.doStartTag();
    iconTag.doEndTag();   // no body content to evaluate for an icon — skip straight to end
}
```

This works identically whether your tag is invoked from a real JSP or through FreeMarker's
bridge — `IconTag` only needs a working `PageContext.getOut()`, which any tag invocation already
guarantees. Read the target tag's source first (`doStartTag()`/`processStartTag()`) to confirm
it returns `SKIP_BODY` for your usage (no body to evaluate) — e.g. `ButtonTag` only does this
when `icon`/`label` are set; with neither, it expects real nested body content you can't easily
drive this way.

### Lighter-weight alternative: plain global FTL variable (no taglib at all)

If you don't need a real JSP tag (no JSP-side usage, no `body-content`, just a helper object or
value you want visible from every display template), skip the whole `.tld`/`taglib-mappings`
mechanism above and implement `com.liferay.portal.kernel.template.TemplateContextContributor`
instead — a much smaller mechanism, unrelated to taglib bridging:

```java
@Component(
    property = "type=" + TemplateContextContributor.TYPE_GLOBAL,
    service = TemplateContextContributor.class
)
public class MyTemplateContextContributor implements TemplateContextContributor {

    @Override
    public void prepare(
        Map<String, Object> contextObjects, HttpServletRequest httpServletRequest) {

        contextObjects.put("myHelper", new MyFreeMarkerHelper());
    }

}
```

`TYPE_GLOBAL` makes it available in every display template; `TYPE_THEME` scopes it to theme
templates only. Whatever object you `put()` becomes callable as `${myHelper.someMethod()}`.
Reach for this only when you don't need real JSP-tag semantics (attributes via `.tld`, body
content, dynamic attributes) — otherwise use the taglib approach above so the same component
works from both JSP and FTL.

---

## 5. Extending a built-in taglib

You cannot add a tag into `liferay-ui.tld`/`liferay-aui.tld`/`liferay-clay.tld` themselves —
those ship as part of core/`frontend-taglib-clay` and aren't editable from a workspace module,
and a `.tld` isn't merge-extensible: there's no mechanism for a second `.tld` to contribute
extra `<tag>` entries into an existing taglib's URI. **Registering a `.tld` is mandatory for
every JSP custom tag, no exceptions** — subclassing a base tag class only gets you a reusable
*handler class*; the JSP container still won't know it's callable as a tag unless some `.tld`
maps a `<name>`/`<tag-class>` pair to it. "Extending" in practice means one of:

- **Subclass the base tag class, ship it under your own `.tld`/prefix.** Liferay's own tags
  are often built on a `Base*Tag` class (e.g. `aui:fieldset` →
  `com.liferay.taglib.aui.base.BaseFieldsetTag`). Extend that base class in your own module,
  override what you need, then declare it in **your own** `.tld` with **your own** prefix (per
  Section 4) — e.g. `<my:fieldset>`, never `<aui:fieldset>` or a new tag added to `aui:`. This
  reuses Liferay's rendering/validation logic without touching the original taglib; check
  `util-taglib/src/com/liferay/taglib/<lib>/base/` for the base classes available for a given
  tag family.
- **JSP fragment override (Look and Feel "custom JSPs" hook).** Some tags render via a
  `start.jsp`/`end.jsp` resolved by path (e.g. `aui:fieldset` → `getStartPage()` returns
  `/html/taglib/aui/fieldset/start.jsp`). Liferay's `customJspBag` mechanism lets a hook
  override that JSP path portal-wide. This changes the tag's output for **every** caller across
  the entire portal — high blast radius, generally avoid unless you specifically need to change
  shared/global behavior, not just your own usage.
- **For FTL global macros** (`clay`, `liferay`): you can't modify what they already expose, but
  you can sit alongside them — your own taglib + `taglib-mappings.properties` (Section 4) adds a
  new globally-available `<@alias...>` namespace without touching Liferay's. This is the
  supported, additive way
  to "extend" the FTL namespace.

In short: prefer *composition* (your own tag/macro that wraps or reuses Liferay's pieces) over
trying to modify the original taglib in place.

---

## 6. Mounting a real React component from a custom taglib

A custom tag (Section 4) isn't limited to hand-written `jspWriter.write(...)` HTML — it can mount
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

---

## 7. Calling methods on an object whose real type isn't exported (reflection)

A tag attribute's *declared* type doesn't have to match the *live* object's real class — FTL can
pass any object through as `java.lang.Object`. This matters because some objects you want a tag
to inspect (the FTL display-template's own `entry`/`document` loop variables, in particular) have
a concrete type that lives in a non-exported `internal` package of another OSGi bundle — your
module can never compile against it, so a typed setter is impossible no matter how the value
reaches the tag.

**Confirm this before assuming reflection is needed** — check whether the concrete class is in a
package ending in `.internal.` (Liferay's bnd convention auto-excludes `*.internal.*` from
`Export-Package`) by finding it in `liferay-portal` source and checking for a sibling
`Export-Package` override:

```bash
find "$LIFERAY_PORTAL" -name "ConcreteClassName.java"
# package com.liferay.foo.web.internal.bar.ConcreteClassName  → not exported, reflection needed
# package com.liferay.foo.api.bar.ConcreteClassName           → exported, just import + cast
```

If it's genuinely internal, reflection still works *despite* the export restriction — OSGi's
class-space rules govern which packages your bundle's classloader can resolve by name
(`import`/`Class.forName`), not whether you can call a method on an object reference you already
hold. `target.getClass().getMethod(...)` resolves against the object's own runtime class, already
loaded by *its* bundle's classloader, so it works as long as the method itself is `public`:

```java
protected Object invoke(Object target, String methodName) {
    if (target == null) {
        return null;
    }

    try {
        Method method = target.getClass().getMethod(methodName);

        return method.invoke(target);
    }
    catch (Exception exception) {
        return null;
    }
}

protected String invokeString(Object target, String methodName, String defaultValue) {
    Object value = invoke(target, methodName);

    return (value != null) ? value.toString() : defaultValue;
}
```

Add `invokeBoolean`/`invokeLong`/`invokeList` the same way, typed to each getter's actual return
type. For a tag attribute that needs to accept a value that's sometimes a real object and
sometimes a different placeholder type (e.g. the FTL falls back to `""` when no matching document
exists at this row index), declare the attribute as `java.lang.Object` too and `instanceof`-check
in the setter — a strictly-typed attribute fails to bind through FreeMarker's JSP bridge the
moment the FTL passes something of a different runtime type:

```java
public void setDoc(Object doc) {
    _doc = (doc instanceof Document) ? (Document)doc : null;
}
```

**Tradeoffs to weigh before reaching for this:**
- It's fragile/version-coupled — a method rename in a future Liferay release breaks silently at
  runtime (catches as `NoSuchMethodException`, falls back to the default), not at compile time.
- It only makes sense when the alternative is genuinely worse — e.g. having the FTL pre-extract
  every needed value into a `Map` and pass that instead, duplicating logic the FTL has no good way
  to express (URL resolution, permission checks, type-name matching) outside the tag.
- If the type is *not* actually internal/non-exported, don't reach for reflection at all — just
  import the real type and call it directly.

---

## 8. Quick decision guide

| You're in... | Need a component | Use |
|---|---|---|
| `.jsp` | Clay component (button, icon, dropdown) | `<liferay-frontend:...>` / `<clay:...>` taglib |
| `.jsp` | Search results table/list | `<liferay-ui:search-container>` |
| `.jsp` | Form input | `<aui:input>` / `<aui:select>` (check deprecation first) |
| `.ftl` (display template) | Clay component | `<@clay.xxx>` — pre-bound, no import |
| `.ftl` (display template) | i18n string | `<@liferay.language key="..." />` |
| `.ftl` (display template) | Something only `liferay-ui`/`aui` has, with real logic | `<@liferay_ui.xxx>` / `<@liferay_aui.xxx>` — bridge, use sparingly |
| `.ftl` (display template) | A piece of UI needing local state (dropdown, modal, fetch call) shared across sibling Display Template script-files | Custom taglib whose tag mounts a real React component (Section 6) — not `<#macro>`/`<#import>`, which fails across separate DDMTemplate script-files |
| custom tag | Needs a value derivable from `RenderRequest`/`ThemeDisplay`/a shared request attribute | Resolve it inside the tag itself (Section 6) — don't have the FTL recompute and pass it as a parameter |
| custom tag | Needs to call a getter on an FTL loop variable (`entry`, `document`, ...) whose concrete type is in an `*.internal.*` package | Reflection helpers (Section 7) — confirm the type really is non-exported first |
| `.ftl` (display template) | Two or more `renderReact()`-backed tag calls (or one such call alongside other static markup) as siblings | Wrap each in its own `<div>` (Section 6's "Critical pitfall") — sharing a parent lets whichever mounts first wipe out everything else under that parent |
| `.ftl` (display template) | Modal, fieldset, or other "this should be a tag" markup | Plain HTML + Clay's own CSS classes (`.modal`, `.fieldset`, `.legend`) — confirm classes via the live `clay.css`, not a custom `<style>` block |
