---
name: liferay-data-engine-form-rules
description: >
  Investigate DataLayout.dataRules, dependent-field show/hide/enable/disable/setRequired rules, DDM expression grammar and missing Rules tabs. Covers Document Type/Journal allowRules restrictions, Forms differences, unknown REST payload shapes and permission-gated test PATCHes.
---

# Liferay Data Engine form rules

Use for native dependent-field UI rules, not field-validation dropdown options
or a backend guarantee. This is extracted from the original DDM validation skill.

## Workflow

1. Resolve the consuming workspace and inspected Liferay release/source.
2. Identify the content type and builder: Document Types and Journal have no
   Rules sidebar in the source-traced implementation; standalone Forms differs.
3. Check `DataLayoutBuilderDefinition.allowRules()` and the tag's sidebar panel
   construction before assuming a missing tab is a navigation problem.
4. Use supported DDM expression functions/operators. The confirmed Java rule
   example is `setRequired('paginationStartParameterName', equals(getValue('pagination'), true))`.
5. Obtain canonical REST JSON from a genuinely supported builder plus a GET;
   do not translate Java action strings into a guessed REST payload.
6. If a direct test PATCH is needed, ask the user for **explicit permission**
   first, even on a disposable resource; inspect the round-trip and restore
   the original value only within the approved test scope.

## Critical constraints

- DDM uses a custom ANTLR4 expression grammar, not MVEL/JEXL. No `if/else`,
  no ternary `?:`, and no unary `!`; `not` is prefix-only.
- `&&`/`and`, `||`/`or`, comparisons, arithmetic, parentheses, literals,
  arrays, identifiers and function calls are supported in the traced grammar.
- `getValue('OtherField')` is confirmed in annotation rule expressions; that
  does not establish the REST `actions`/`conditions` map serialization.
- Exact populated `dataLayout.dataRules` REST JSON remains unverified. So do
  REST persistence and runtime honoring of rules for `content.type=document-library`.
- Document Library inherits `allowRules=false`; Journal explicitly disables it.
  Standalone Forms uses its separate older builder with `allowRules: true`.
- Dynamic `setRequired` is frontend-only: it does not change the static required
  DB flag seen by `DDMFormValuesValidatorImpl`. Direct API calls bypass it.

## References

- [Rules evidence, grammar, REST uncertainty and builder restrictions](references/rules-and-grammar.md)
- [Backend field validation](../liferay-ddm-field-validation/SKILL.md) — enforce actual invariants; its old `if(...)` illustration is conceptual only.
- [globalJS editor extensions](../liferay-globaljs-editor-extension/SKILL.md) — browser fallback when native rules are unavailable.

References describe another consuming workspace and inspected source snapshot;
resolve current paths and release before applying them. No mutation is implied.
