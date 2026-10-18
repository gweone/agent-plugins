# Site targeting and batch data format

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Targeting a specific site — the actual mechanism, verified

Confirmed by reading `VulcanBatchEngineTaskItemDelegateAdaptor._applyParamConverters`
(`portal-vulcan-impl/.../internal/batch/engine/VulcanBatchEngineTaskItemDelegateAdaptor.java`):

```java
else if (key.equals("siteId") && (value != null)) {
    parameters.put(key, GroupUtil.getGroupId(_company.getCompanyId(), String.valueOf(value), _groupLocalService));
}
```

Put a `"siteId"` key in the batch file's `configuration.parameters` object. `GroupUtil.getGroupId`
(`portal-vulcan/.../util/GroupUtil.java`) resolves it by trying, in order: **group key** (e.g.
`"Guest"`), **numeric group ID** (e.g. `"20126"`), then **external reference code** (e.g.
`"L_GUEST"`) — any of the three works. `GroupUtil.getScopeKey()` also recognizes `"scopeKey"` and
`"siteExternalReferenceCode"` as aliases for the same thing, but `"siteId"` is what every actual
production code path (`_applyParamConverters`) checks for — use that key name.

```json
{
  "configuration": {
    "className": "com.liferay.object.rest.dto.v1_0.ObjectEntry",
    "parameters": {
      "containsHeaders": "true",
      "createStrategy": "UPSERT",
      "siteId": "L_GUEST",
      "taskItemDelegateName": "C_QAFieldCoverage",
      "updateStrategy": "UPDATE"
    },
    "taskItemDelegateName": "C_QAFieldCoverage"
  },
  "items": [ ... ]
}
```

No real-world sample in `liferay-portal` actually sets `siteId` (every example imports
company-scoped resources) — this was derived directly from the adaptor source, not copied from a
working sample.

**Update — confirmed working end-to-end against the live Guest site.** Built a real batch CX
(`client-extensions/sharpps-objects-batch/`) with `"siteId": "L_GUEST"` in two
`ObjectEntry`-importing files (targeting site-scoped custom objects), deployed it, and verified
via direct REST query afterward that `dateModified` on the live Guest-scoped entries updated to
the exact deploy timestamp — the import genuinely ran and wrote to Guest. Confirmed in the same
test: company-scoped `ObjectDefinition`/`ObjectRelationship` imports (no `siteId` needed) and
relationship resolution via `objectDefinitionExternalReferenceCode1`/`2` (using the source object-definition ERCs) both worked correctly too. The only thing that stood between "should work per the
source" and "actually works" was the `assemble:` yaml block in [mandatory assemble block](packaging.md) — once that was in
place, all four `*.batch-engine-data.json` files processed cleanly with zero errors.

## `*.batch-engine-data.json` format

```json
{
  "configuration": {
    "className": "<fully.qualified.dto.ClassName>",
    "parameters": {
      "containsHeaders": "true",
      "createStrategy": "INSERT | UPSERT",
      "updateStrategy": "UPDATE | PARTIAL_UPDATE",
      "importStrategy": "ON_ERROR_FAIL | ON_ERROR_CONTINUE",
      "taskItemDelegateName": "DEFAULT | <ObjectShortNameWithCPrefix>",
      "siteId": "<optional — groupKey | numeric groupId | ERC>"
    },
    "taskItemDelegateName": "DEFAULT | <same value as above>"
  },
  "items": [ { /* one DTO matching className per array entry */ } ]
}
```

- `taskItemDelegateName` is duplicated at both the top `configuration` level and inside
  `parameters` in every real sample — set both.
- For **Object Entries**, `taskItemDelegateName` is the object's REST short name **with its `C_`
  prefix**, e.g. `"C_QAFieldCoverage"` (not the bare object name) — confirmed from real examples
  (`liferay-ticket-workspace`'s `"C_J3Y7Ticket"`).
- Files are read in natural-sort filename order — prefix with numbers (`00-`, `01-`, `02-`...) to
  sequence dependencies (definitions before relationships before entries), matching every real
  sample's convention.
- Picklist-valued fields use `{"key": "...", "name": "..."}`; Multiselect-valued fields use an
  array of such objects in this format (unlike the Site Initializer engine's `object-entries/`
  files, where Multiselect needs a plain string array — see [initializer multiselect caveat](../../liferay-site-initializer/references/limitations.md). **Don't
  assume the two engines share a value-shape convention; verify per-engine.**
