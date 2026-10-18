---
name: liferay-portal-source
description: Locate, orient, and search a Liferay Portal source checkout. Use to find upstream classes, portlets, OSGi registrations, Service Builder entities, properties, JSPs, or frontend implementations and verify version-specific APIs; ask before bootstrapping a missing checkout.
---

# Liferay source navigation

Use when the task needs upstream implementation evidence. The source tree
is **not bundled** with this plugin and has no fixed absolute path.
This is not a catch-all prerequisite for every Liferay task.

## Workflow

1. Resolve the current workspace root, then check its sibling
   `liferay-portal` directory. Validate `modules/`, `portal-impl/`, or
   `portal-kernel/`; never reuse a remembered machine-specific path.
2. If absent, ask whether the user has a checkout elsewhere. **Do not
   clone or bootstrap silently.** Obtain confirmation before creating a
   new source checkout and confirm the target release/ref first.
3. Orient on the actual checkout/version before drawing conclusions.
   Layouts and APIs differ across releases and CE vs DXP; enterprise-only
   modules may not exist in a CE tree.
4. Search the relevant product/module first. Trace class → OSGi component →
   public API/callers, or TLD → backing class, rather than guessing signatures.
5. Report evidence from the target version. Source paths in other feature
   guides are lookup hints, not proof that a checkout matches the runtime.
6. For requested code changes, avoid generated files, inspect bundle exports
   and versions, use the project's Gradle wrapper, and format as required.
   Source lookup does not authorize building, deploying, or changing a runtime.

## Lookup

| Need | Reference |
|---|---|
| Dynamic path resolution, existing checkout, approved shallow bootstrap, orientation | [Source checkout](references/source-checkout.md) |
| Directory/module layout, classes, portlets, DS, service.xml, properties | [Layout and targeted searches](references/layout-and-search.md) |
| Ant vs Gradle, OSGi, frontend resources, SQL, common tasks and gotchas | [Platform patterns](references/platform-patterns.md) |

## Related skills

- [liferay-jsp-taglibs](../liferay-jsp-taglibs/SKILL.md): verify JSP tags against TLDs and backing classes.
- [liferay-freemarker-macros](../liferay-freemarker-macros/SKILL.md): verify FTL macro namespaces and JSP bridge aliases.
- [liferay-site-initializer](../liferay-site-initializer/SKILL.md): initializer engine traces.
- [liferay-batch-client-extension](../liferay-batch-client-extension/SKILL.md): batch delegate verification.
