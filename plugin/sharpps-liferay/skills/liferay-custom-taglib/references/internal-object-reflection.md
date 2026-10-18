Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

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
