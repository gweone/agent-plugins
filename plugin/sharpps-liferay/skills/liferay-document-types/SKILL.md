---
name: liferay-document-types
description: Import Liferay Document Types, DocumentDataDefinitionType, DocumentMetadataSet, Data Engine field schemas, and documentType contentFields with metadata-first batch bootstrap and fieldReference values.
---

# Liferay Document Types

Canonical shared workflow for Documents & Media metadata sets, type schemas,
and values. This extracts the initializer and batch skills' live-tested
material; it does not establish binary-document batch import support.

## Workflow

1. Confirm source/target release, company/site, metadata sets, and Document Types.
   Resolve [Portal source](../liferay-portal-source/SKILL.md) for trace checks;
   paths in references are external checkout/consuming-workspace precedents.
2. Read the [schema bootstrap](references/schema-bootstrap.md). Export real
   `dataDefinitionFields` using metadata-set/type GETs; reuse them verbatim.
   Data Engine `fieldType`/`customProperties` is not old Web Content DDM JSON.
3. Prepare a [batch CX](../liferay-batch-client-extension/SKILL.md) with mandatory
   assemble packaging. Create the **metadata set first**, in its own file,
   using `DocumentMetadataSet` and the target `parameters.siteId`.
4. Use **`createStrategy: INSERT` only; omit `updateStrategy`** for both schemas.
   The tested delegate rejects UPDATE despite PUT-by-ERC REST methods.
   Include **`availableLanguages: ["en-US"]`** on each item.
5. Obtain explicit authorization before deployment. After the metadata set
   exists, query its actual auto-assigned **numeric ID**; do not predict it.
   Then create `DocumentDataDefinitionType` in a second file with
   `documentMetadataSetIds: [<resolved ID>]` and its own fields as applicable.
6. Treat this as **one-time schema bootstrap**, not cleanly idempotent redeploy:
   reruns produce per-item duplicate-ERC errors (other files were unaffected
   in the observed run). Do not hide these as proof of a successful update.
7. Populate [document sidecars and values](references/document-values.md) only
   after the type exists. Use `documentType.name` and **`fieldReference`**, not
   generated internal `name`; the wrong key silently saves empty values.
8. Preserve internal option keys, not labels, for select/multiselect and grid
   fields; grid rows and columns each use their exported `value` keys.
   Cross-import image/article entity references are unreliable: leave unset
   rather than fake IDs. Read back actual saved fields, not just type assignment.

## Lookup

| Need | Reference |
|---|---|
| Resource names, source traces, export GETs, metadata-first recipe | [Schema bootstrap](references/schema-bootstrap.md) |
| INSERT-only, availableLanguages, duplicates, numeric metadata-set IDs | [Bootstrap constraints](references/schema-bootstrap.md#metadata-first-schema-bootstrap) |
| Complete sidecar JSON, fieldReference failure, grid example, entity refs | [Document values](references/document-values.md) |
| Select/multiselect option-key caution | [Option keys](references/document-values.md#select-and-multiselect-option-keys) |

## Related skills

- [Batch Client Extension](../liferay-batch-client-extension/SKILL.md): schema import packaging and execution.
- [Site Initializer](../liferay-site-initializer/SKILL.md): document resources after schema bootstrap.
- [Data Engine form rules](../liferay-data-engine-form-rules/SKILL.md): related form-rule work.
