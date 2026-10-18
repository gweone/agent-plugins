---
name: liferay-react-taglib
description: Mount React from a Liferay Java JSP/FTL custom tag using ReactRenderer, ComponentDescriptor, and Snapshot. Use for named npm exports, disappearing sibling components, exclusive mount parents, live RenderRequest state, or tag service lookup.
---

# React mounting from Liferay tags

This is Java-side rendering integration, not the npm/scaffold workflow in
[liferay-react-module](../liferay-react-module/SKILL.md).

## Workflow

1. Verify the target renderer/tag APIs with
   [liferay-portal-source](../liferay-portal-source/SKILL.md), and set up
   [custom registration](../liferay-custom-taglib/SKILL.md) when needed.
2. Resolve `"{ExportName} from <npm-package-name>"` against a named export
   from the module's root resources barrel; check the actual package name.
3. Use `Snapshot<ReactRenderer>` for services needed by directly constructed
   tag instances. JSP/FTL-created tags are not DS-managed `@Reference` consumers.
4. Give **every React-backed tag an exclusive parent element**. The renderer
   mounts into its placeholder's parent and takes over all children. Shared
   parents can erase sibling mounts or unrelated static markup.
5. Resolve page-level state from live RenderRequest/RenderResponse and shared
   request attributes inside the tag; keep tag attributes for genuinely
   per-row/call-site data.
6. Treat HTML props as strings. Only render trusted/sanitized HTML raw;
   `html-react-parser` is not sanitization. Keep mutable formatters local
   per call, not static across concurrent requests.
7. Verify multiple mounts and surrounding content after client hydration.
   ReactRenderer is client-side-only: it does not provide SSR/SEO content.

## Lookup

- [Renderer API, named exports, Snapshot, and HTML props](references/react-mounting.md)
- [Exclusive-parent mounting pitfall](references/react-mounting.md#critical-pitfall-every-renderreact-call-needs-its-own-exclusive-parent-div)
- [Live request/response lookup](references/react-mounting.md#retrieving-the-live-renderrequestrenderresponse-from-a-tag)
- [Concurrent-request mutable-state pitfall](references/react-mounting.md#pitfall-dont-share-mutable-per-call-state-across-a-static-field)

## Related skills

- [liferay-freemarker-macros](../liferay-freemarker-macros/SKILL.md): FTL call sites.
- [liferay-management-toolbar-search-container](../liferay-management-toolbar-search-container/SKILL.md): toolbar React integration.
