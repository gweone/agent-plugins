---
name: liferay-ddm-field-validation
description: >
  Add or debug DDM/Data Engine field validation, customProperties.validation, regex/email expressions, DDMValidation dropdown options, and DDMExpressionFunction backend extensions. Distinguish server enforcement from globalJS UX and dataRules.
---

# Liferay DDM field validation

Use for field-level validation in Data Engine-backed forms, including Document
Types, Forms and applicable Object integrations. Verify the target integration
and release; the references retain source-traced and live Document Type evidence.

## Workflow

1. Resolve the consuming workspace and target Liferay source/version with
   [liferay-portal-source](../liferay-portal-source/SKILL.md).
2. For one field, prefer `customProperties.validation`: start from the verified
   email JSON, then verify any new expression in its actual evaluation context.
3. For a reusable named Validation-dropdown option, implement `DDMValidation`.
   Its binding is the **dataType**, not field type, entity, or one Document Type.
4. For database/external checks beyond expression functions, investigate a
   `DDMExpressionFunction` alongside the validator; do not invent a CX hook.
5. Verify backend enforcement for the target save path, separately from browser
   behavior. Direct REST/JSONWS must not bypass a required invariant.

## Critical constraints

- Declarative validation needs no Java; custom validator/function registrations
  need OSGi. A globalJS Client Extension provides browser UX, not backend checks.
- A string-scoped `DDMValidation` becomes available instance-wide on string-backed
  fields; ranking orders choices and does not scope the component to one field.
- The historical `if (dt_category.value() == 'form') { ... }` example is
  **conceptual, not executable verified DDM syntax**. The grammar has no `if/else`
  or ternary `?:`; verify supported lookup/functions instead of copying it.
- Dynamic `setRequired`/show/hide rules are a different, frontend-only mechanism.
  Do not treat them as static required flags or backend validation.

## Focused references

- [Declarative JSON, backend conversion and built-in functions](references/declarative-validation.md)
- [Custom component example, dataType binding and ranking](references/custom-validators.md)
- [Backend versus client-extension boundaries and source evidence](references/backend-and-client-boundaries.md)

## Related skills

- [liferay-data-engine-form-rules](../liferay-data-engine-form-rules/SKILL.md) — dataRules, grammar and allowRules restrictions.
- [liferay-globaljs-editor-extension](../liferay-globaljs-editor-extension/SKILL.md) — field DOM, observers and UI submit interception; DOM detail lives there only.

External workspace paths in the references are examples, not files in this plugin.
