Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

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
