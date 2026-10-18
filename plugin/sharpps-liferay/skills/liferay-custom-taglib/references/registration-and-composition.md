Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

The handler example illustrates lifecycle only; escape untrusted label/content before writing HTML.

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
   `<#import>`, which does not provide a shared namespace across independently evaluated
   Portlet Display Template script-files).

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
  [custom registration](registration-and-composition.md)) — e.g. `<my:fieldset>`, never `<aui:fieldset>` or a new tag added to `aui:`. This
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
  you can sit alongside them — your own taglib + `taglib-mappings.properties` ([custom registration](registration-and-composition.md)) adds a
  new globally-available `<@alias...>` namespace without touching Liferay's. This is the
  supported, additive way
  to "extend" the FTL namespace.

In short: prefer *composition* (your own tag/macro that wraps or reuses Liferay's pieces) over
trying to modify the original taglib in place.
