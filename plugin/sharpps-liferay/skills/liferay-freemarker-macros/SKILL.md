---
name: liferay-freemarker-macros
description: Use Liferay FreeMarker FTL macros in display or theme templates. Look up clay/liferay namespaces, JSP taglib bridge aliases, taglib-mappings.properties, missing alias errors, and shared helpers across DDMTemplate script files.
---

# Liferay FreeMarker macros and JSP bridge

Use for consuming macros in `.ftl`, not JSP tag declarations or module scaffolding.

## Workflow

1. Identify whether the template is a display template or theme template;
   confirm its available variables against the target version/source using
   [liferay-portal-source](../liferay-portal-source/SKILL.md).
2. Use pre-bound `clay`/`liferay` helpers where supported. FTL cannot use
   JSP `<%@ taglib %>` declarations.
3. For a bridged JSP tag, inspect `/META-INF/taglib-mappings.properties`.
   The alias is explicitly registered, not derived from the TLD short-name;
   do not guess by replacing hyphens with underscores.
4. Bridge sparingly: verify deprecations and normal JSP-lifecycle assumptions.
   Prefer supported macros; for simple output not suitably covered by one,
   verified Clay markup can be safer than bridging a legacy tag.
5. To share logic across independently evaluated display-template scripts,
   choose a registered custom taglib or a global TemplateContextContributor;
   do not assume file imports provide a shared namespace across scripts.
6. For stateful React-backed tags, use dedicated mount parents; read
   [liferay-react-taglib](../liferay-react-taglib/SKILL.md) before wiring them.

## Lookup

- [Pre-bound macros, alias mappings, bridge limitations](references/macros-and-bridge.md)
- [Tag and deployed CSS verification](../liferay-jsp-taglibs/references/tag-and-css-verification.md)
- [Register a custom JSP/FTL taglib](../liferay-custom-taglib/references/registration-and-composition.md)
- [Global helper vs theme-only helper](../liferay-custom-taglib/references/template-context-contributors.md)

## Related skills

- [liferay-jsp-taglibs](../liferay-jsp-taglibs/SKILL.md): JSP consumer syntax and pitfalls.
- [liferay-custom-taglib](../liferay-custom-taglib/SKILL.md): custom handler/registration.
- [liferay-react-taglib](../liferay-react-taglib/SKILL.md): ReactRenderer and request state.
