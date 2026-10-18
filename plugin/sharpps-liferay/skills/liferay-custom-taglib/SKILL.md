---
name: liferay-custom-taglib
description: Create or extend a Liferay custom JSP/FTL taglib. Use for tag handlers, TLD descriptors, jsp.taglib Provide-Capability, taglib-mappings.properties, composition, TemplateContextContributor helpers, or non-exported FTL object types.
---

# Custom Liferay taglibs and template helpers

A traditional OSGi module is appropriate here: Client Extensions do not
supply JSP handlers or taglib registration.

## Workflow

1. Inspect the target version and existing patterns with
   [liferay-portal-source](../liferay-portal-source/SKILL.md). Determine
   whether callers need JSP-tag semantics or only an FTL helper object.
2. For a real tag, create the handler and TLD. Prefer a module-local tag
   unless concrete cross-module reuse justifies exported/imported packages.
   Escape untrusted values before writing HTML.
3. Register JSP and FTL independently: `jsp.taglib` Provide-Capability for
   JSP discovery; `META-INF/taglib-mappings.properties` for the FTL alias.
   One does not imply the other. Confirm bundle restart after authorized deploy.
4. Compose existing Java tags against the current PageContext rather than
   including a module JSP relative to the portal ROOT request context.
   Check body-content/lifecycle behavior before driving another tag manually.
5. Extend under your own TLD/prefix. Do not try to merge tags into core TLDs;
   portal-wide JSP overrides affect every caller and need separate approval.
6. For FTL-only helpers, consider `TemplateContextContributor.TYPE_GLOBAL`
   vs `TYPE_THEME`. For object attributes, use exported APIs when possible;
   reflection over public methods is a last, version-coupled option only
   after confirming the concrete package really is not exported.

## Lookup

- [Handler, TLD, independent JSP/FTL registration, composition and extension](references/registration-and-composition.md)
- [TemplateContextContributor: global helper alternative](references/template-context-contributors.md)
- [Object-typed attributes and internal-object reflection caveats](references/internal-object-reflection.md)

## Related skills

- [liferay-jsp-taglibs](../liferay-jsp-taglibs/SKILL.md): consume tags from JSP.
- [liferay-freemarker-macros](../liferay-freemarker-macros/SKILL.md): consume FTL aliases.
- [liferay-react-taglib](../liferay-react-taglib/SKILL.md): React-backed tag lifecycle.
- [liferay-react-module](../liferay-react-module/SKILL.md): frontend module toolchain.
