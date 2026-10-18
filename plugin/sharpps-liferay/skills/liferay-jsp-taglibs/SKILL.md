---
name: liferay-jsp-taglibs
description: Use Liferay JSP/JSPF tags such as aui, clay, liferay-ui, and portlet. Look up taglib declarations, attributes, deprecations, Jasper errors, nested-tag restrictions, quote escaping, checkbox values, or JSP-to-tag conversions.
---

# Liferay JSP tag usage

For `.jsp`/`.jspf` consumers. For FTL syntax use
[liferay-freemarker-macros](../liferay-freemarker-macros/SKILL.md).

## Workflow

1. Inspect existing `init.jsp`/`init-ext.jsp` includes before adding duplicate
   taglib declarations. Choose the library for the actual component.
2. Resolve the source/version with
   [liferay-portal-source](../liferay-portal-source/SKILL.md). Verify the tag
   and attributes in its TLD and deprecation in its backing Java class.
3. Prefer a supported tag over copied HTML; search the portal's own JSPs
   for nontrivial picker, chip-list, and form patterns before inventing one.
4. Do not nest a custom tag inside another tag's attribute value; use a
   scriptlet expression. Quote escaping differs between custom-tag
   attributes and raw HTML. Check the reference before moving expressions.
5. Audit JS auto-wiring when changing CSS classes. For checkboxes, set
   submitted `value` and initial `checked` independently when needed.
6. Use ASCII or Unicode escapes in embedded JSP JavaScript to avoid
   encoding corruption. Check `-Werror` and deprecated-tag warnings.
7. Validate the changed JSP in the target workspace's build; building is
   not deployment authorization. Verify rendered markup and behavior.

## Lookup

- [Declarations, library table, attributes, and conversion pitfalls](references/jsp-usage.md)
- [TLD, backing class, and deployed Clay CSS verification](references/tag-and-css-verification.md)

## Related skills

- [liferay-custom-taglib](../liferay-custom-taglib/SKILL.md): create handlers and TLDs.
- [liferay-react-taglib](../liferay-react-taglib/SKILL.md): mount React from a Java tag.
- [liferay-management-toolbar-search-container](../liferay-management-toolbar-search-container/SKILL.md): selection and bulk actions.
