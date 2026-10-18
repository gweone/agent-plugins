# Document sidecars and field values

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

These field-population findings came from the original initializer’s `liferay/dxp:7.4.13.nightly` investigation; re-verify on the target build. Bootstrap the [schema first](schema-bootstrap.md).

Now that the type exists, a document's `<file>.metadata.json` (the *existing*, already-documented
   sidecar file convention under `documents/`) can populate it on creation:
   ```json
   {
       "viewableBy": "Anyone",
       "documentType": {
           "name": "Metadata Form",
           "contentFields": [
               {"fieldReference": "Name", "contentFieldValue": {"data": "..."}},
               {"fieldReference": "Color", "contentFieldValue": {"data": "2BA676"}}
           ]
       }
   }
   ```

**The one bug that will burn you here, confirmed by reading `DDMFormValuesUtil` source directly:
content fields must be keyed by `fieldReference`, not `name` — and getting this wrong produces zero
errors, just silently empty values.** `DocumentResourceImpl` resolves the Document Type by name,
finds its DDM structure(s) via `DLFileEntryTypeUtil.getDDMStructures`, and converts your
`contentFields` via `DDMFormValuesUtil.toDDMFormValues`
(`DDMFormValuesUtil.java:156-174` (`$LIFERAY_PORTAL/modules/apps/headless/headless-delivery/headless-delivery-api/src/main/java/com/liferay/headless/delivery/dto/v1_0/util/DDMFormValuesUtil.java#L156-L174`))
— which groups incoming fields into a map keyed by `contentField.getFieldReference()`, then looks
each one up by `ddmFormField.getFieldReference()`. If your JSON instead uses `"name":
"Text96664356"` (the field's internal generated name, which is what GET responses show right next
to `fieldReference` and is easy to reach for instead), every field maps to a `null` key, the lookup
never matches anything, and the document gets the correct Document Type assigned with every field
present but empty — looking exactly like "the import silently didn't work" with nothing in any log
to suggest why. Always use `fieldReference` (the human-meaningful key like `"Name"`/`"Color"`), not
`name` (the auto-generated internal one like `"Text96664356"`), when writing `contentFields`.

**A `grid` field's value must use the options' internal `value` keys for both axes, not their
labels** — confirmed via `GridDDMFormFieldValueValidator`
(`GridDDMFormFieldValueValidator.java` (`$LIFERAY_PORTAL/modules/apps/dynamic-data-mapping/dynamic-data-mapping-form-field-type/src/main/java/com/liferay/dynamic/data/mapping/form/field/type/internal/grid/GridDDMFormFieldValueValidator.java`)),
which validates the JSON object's keys against the row options' `value`s and its values against the
column options' `value`s. A row labeled "Content" with internal value `"Option63937194"` and a
column labeled "Office" with internal value `"Option77676455"` must be written as
`{"Option63937194": "Option77676455"}`, not `{"Content": "Office"}` — the latter fails with
`DDMFormValuesValidationException$MustSetValidValue` (the error names the field but gives no hint
that label-vs-value is the issue). Find the real option value keys in the field's
`customProperties.rows`/`customProperties.columns` arrays (each option has both a `label` and a
`value`) when copying source field definitions per the [schema bootstrap recipe](schema-bootstrap.md#metadata-first-schema-bootstrap).

**Fields that reference *other* entities (an image picker, a structured-content/journal-article
reference) don't have a reliable way to resolve against a freshly-imported target and are best left
unset** rather than faked — there's no stable cross-import ID for "the image that happened to exist
on the source site" without also reproducing that exact document, and guessing wrong fails silently
the same way the `fieldReference` bug does.

## Select and multiselect option keys

Preserve the exported schema’s internal option keys for select/multiselect fields, not display labels. Do not assume the Object Entry shapes used by the initializer and batch engines apply to document `contentFields`; those engines already differ for Object multiselect values. Reuse the source schema and verify the saved document values, rather than inventing a value shape.
