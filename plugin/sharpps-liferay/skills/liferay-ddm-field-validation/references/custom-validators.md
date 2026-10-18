# Custom DDMValidation components

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

## 3. Custom validator (`DDMValidation` OSGi component) — new dropdown option, instance-wide

Only build this when you want a NEW named, reusable validator to appear as a selectable option
in the field settings' "Validation" dropdown (same UI slot as "Email"/"URL"/"Matches"), instead
of hand-writing a raw expression once on one field.

Interface:
`DDMValidation` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-api/src/main/java/com/liferay/dynamic/data/mapping/form/validation/DDMValidation.java`)

```java
@Component(
	property = {
		"ddm.validation.data.type=string",
		"ddm.validation.ranking:Float=4"
	},
	service = DDMValidation.class
)
public class IsEmailDDMValidation implements DDMValidation {

	public String getName() {
		return "email";
	}

	public String getLabel(Locale locale) {
		return _language.get(
			ResourceBundleUtil.getModuleAndPortalResourceBundle(locale, getClass()),
			"is-an-email");
	}

	public String getTemplate() {
		return "isEmailAddress({name})";
	}

	public String getParameterMessage(Locale locale) {
		return StringPool.BLANK;
	}
}
```

Real OOTB example this was copied from:
`IsEmailDDMValidation.java` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-form-evaluator-impl/src/main/java/com/liferay/dynamic/data/mapping/form/evaluator/internal/validation/IsEmailDDMValidation.java`).
Other OOTB implementations live in the same package — copy whichever is closest to the new rule
(e.g. `MatchesDDMValidation` for a parameterized regex) rather than starting from scratch.

### How it binds to a field — confirmed by tracing the consumer, not assumed

`DDMFormTemplateContextFactoryImpl` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-form-renderer/src/main/java/com/liferay/dynamic/data/mapping/form/renderer/internal/DDMFormTemplateContextFactoryImpl.java#L152-L156`)
builds a `ServiceTrackerMap<String, List<DDMValidation>>` keyed by the `ddm.validation.data.type`
component property (grouped by **data type** — `string`/`integer`/`double`/`date`/etc — **not**
by DDM Form Field Type like `text`/`select`), ordered by `ddm.validation.ranking`, and puts the
result into the template context
(`line 354` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-form-renderer/src/main/java/com/liferay/dynamic/data/mapping/form/renderer/internal/DDMFormTemplateContextFactoryImpl.java#L354`))
that renders the field settings' Validation dropdown. `getTemplate()`'s `{name}` placeholder is
substituted with the actual field name at runtime — the resulting string is exactly what ends up
as `customProperties.validation.expression.value` from
[declarative validation](declarative-validation.md), so it goes through the same
`DDMFormValuesValidatorImpl`, same backend guarantee.

**Binding key point:** you bind to `dataType` (string/integer/double/date/boolean/...), not to
one specific field type or one specific Document Type/Object. A new `string`-scoped validator
becomes selectable on every string-backed field across the whole instance at once — there is no
way to scope a `DDMValidation` component to a single Document Type or a single field.

**Complexity ceiling:** `getTemplate()` can only call DDM Expression Language functions. If the
rule needs something an expression can't express (a uniqueness check against the database, a
call to an external system), pair this with a custom `DDMExpressionFunction` OSGi component too
— same module, one more extension point, not covered in depth here.
