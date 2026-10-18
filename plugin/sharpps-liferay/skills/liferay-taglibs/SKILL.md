---
name: liferay-taglibs
description: Choose the appropriate Liferay taglib pattern for JSP tags, FreeMarker macros, custom TLD registration, Java-to-React mounting, or Clay tag/CSS verification. Use when the integration mechanism is unclear; focused skills provide implementation details.
---

# Liferay taglib lookup

Choose the task below. This selector is not a prerequisite for every JSP/FTL edit.
Resolve the target version and source checkout with
[liferay-portal-source](../liferay-portal-source/SKILL.md) when verifying APIs.

| Task / search terms | Focused skill |
|---|---|
| JSP/JSPF, aui, clay, liferay-ui, declarations, attributes, Jasper errors | [liferay-jsp-taglibs](../liferay-jsp-taglibs/SKILL.md) |
| FTL display/theme templates, macro namespaces, JSP bridge aliases | [liferay-freemarker-macros](../liferay-freemarker-macros/SKILL.md) |
| Create/extend a tag, handler/TLD, OSGi registration, shared FTL helper | [liferay-custom-taglib](../liferay-custom-taglib/SKILL.md) |
| ReactRenderer, ComponentDescriptor, Snapshot, disappearing sibling mounts | [liferay-react-taglib](../liferay-react-taglib/SKILL.md) |
| React portlet/module scaffold, npm exports, Babel/Gradle toolchain | [liferay-react-module](../liferay-react-module/SKILL.md) |
| Search-container selection, management toolbar, bulk actions, propsTransformer | [liferay-management-toolbar-search-container](../liferay-management-toolbar-search-container/SKILL.md) |

## Shared verification

[Tag, macro, and deployed Clay CSS verification](../liferay-jsp-taglibs/references/tag-and-css-verification.md)
contains TLD/backing-class searches and live CSS checks, including label flex
direction and dropdown indicator spacing.

Prefer an existing supported tag/macro over equivalent hand-written HTML,
but verify availability and deprecation first. Do not invent `clay:modal`
or `<@clay.modal>`; use the appropriate React component or verified Clay
markup when no supported server-side tag covers the need.

For FTL, bridge JSP tags sparingly: a deprecated or lifecycle-dependent tag
is not automatically a good choice simply because it can be bridged.
