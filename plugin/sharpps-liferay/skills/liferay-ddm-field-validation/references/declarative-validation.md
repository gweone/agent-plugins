# Declarative DDM field validation

[Skill workflow and reference index](../SKILL.md)

> Evidence scope: retained from source tracing and live debugging in an earlier consuming
> Liferay workspace, not executed or re-verified in this plugin repository. Resolve the
> current workspace, target release and applicable local rules before applying examples.
> `modules/search` (`sharpps-search`), `client-extensions/liferay-global-extension`,
> initializer paths, `.claude/rules/cx.md`/`CLAUDE.md`, `configs/local`, `bundles`, and
> container `liferay-dev` are external workspace examples, not plugin-local files or links.
> Resolve `$LIFERAY_PORTAL` with [liferay-portal-source](../../liferay-portal-source/SKILL.md)
> for source citations; line numbers describe the inspected snapshot, not every release.
> Headings retain original numbering for provenance; navigation uses topical links.

## 1. Two distinct mechanisms — know which one you need

| | Declarative expression validation | Custom `DDMValidation` type |
|---|---|---|
| Where it lives | `customProperties.validation` on one field | New OSGi component, registered instance-wide |
| Needs Java/OSGi? | No | Yes |
| Scope | That one field only | Every field sharing the same `dataType`, portal-wide |
| Use when | You need *a* validation rule (built-in or a regex) on *this* field | You want a NEW reusable, named option to appear in the "Validation" dropdown |

Both are enforced by the same backend validator, so both are real server-side guarantees, not
just UI polish. See [backend/client boundaries](backend-and-client-boundaries.md)
for Client Extension DOM tricks, which are *not* backend-enforced.

## 2. Declarative field validation (no code)

Confirmed end-to-end from source, not from docs:

- `customProperties.validation` on a `DataDefinitionField` is converted into a real
  `DDMFormFieldValidation` by
  `DataDefinitionDDMFormUtil._getDDMFormFieldValidation` (`$LIFERAY_PORTAL/modules/apps/data-engine/data-engine-rest-api/src/main/java/com/liferay/data/engine/rest/dto/v2_0/util/DataDefinitionDDMFormUtil.java#L166-L198`),
  dispatched whenever a `customProperties` key's registered settings field type is
  `"validation"` (`dispatch site, line 292-298` (`$LIFERAY_PORTAL/modules/apps/data-engine/data-engine-rest-api/src/main/java/com/liferay/data/engine/rest/dto/v2_0/util/DataDefinitionDDMFormUtil.java#L292-L298`)).
- That `DDMFormFieldValidation` is enforced **server-side**, unconditionally, by
  `DDMFormValuesValidatorImpl` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-validator/src/main/java/com/liferay/dynamic/data/mapping/validator/internal/DDMFormValuesValidatorImpl.java`)
  — the one shared validator the whole Data Engine funnels through (Document Types, Objects,
  Forms all use it), not something wired into just one UI screen. It cannot be bypassed by
  calling headless REST or JSONWS directly instead of the UI form.

### JSON shape (verified working against a live Document Type field)

```json
{
  "fieldType": "text",
  "name": "dt_owner_email",
  "customProperties": {
    "fieldReference": "dt_owner_email",
    "dataType": "string",
    "validation": {
      "expression": {
        "name": "expression",
        "value": "isEmailAddress(dt_owner_email.value())"
      },
      "errorMessage": {"en_US": "Enter a valid email address"}
    }
  }
}
```

The original example `if (dt_category.value() == 'form') { ... }` is **conceptual,
not executable verified DDM syntax**. It illustrates a cross-field requirement only;
DDM's custom ANTLR grammar has **no `if/else` and no ternary `?:`**. Do not copy that
example into a payload. Use supported expression functions/operators and verify field
lookup syntax in the target validation context before claiming a conditional rule works.
The live email JSON above was verified; that does not verify arbitrary conditional syntax.
A properly verified validation expression is the backend layer, unlike client-side
[dataRules](../../liferay-data-engine-form-rules/references/rules-and-grammar.md).

**Built-in expression functions already registered as OOTB `DDMValidation` types** — use these
directly instead of reinventing them: `isEmailAddress()`, `isURL()`, `matches()` (regex), plus
comparison/date-range ones (`IsEqualTo`, `IsGreaterThan`, `IsLessThan`, `Contains`,
`FutureDates`, `PastDates`, etc.). Full list and their exact `getTemplate()` strings:
`validation package` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-form-evaluator-impl/src/main/java/com/liferay/dynamic/data/mapping/form/evaluator/internal/validation/`).
