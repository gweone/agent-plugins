# Folder ERC resolution, URL tokens and review exceptions

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

## `rootFolderId` → `rootFolderERC` + ERC-based URL tokens: fixed, full recipe

Unlike `definitionId` (a single entity type, `DDMStructure`), the FolderTree widget navigates
**three different folder model types** depending on the configured `folderEntryClassName` —
`DLFolder`, `JournalFolder`, `KBFolder` — each with its own ERC-lookup mechanism and even its own
primary-key getter name (`KBFolder.getKbFolderId()`, not `getFolderId()`). A new
`org.sharpps.search.definition.FolderResolver` OSGi service
(`FolderResolver.java` (`modules/search/src/main/java/org/sharpps/search/definition/FolderResolver.java`),
`FolderResolverImpl.java` (`modules/search/src/main/java/org/sharpps/search/definition/internal/FolderResolverImpl.java`))
dispatches by `folderEntryClassName` to the right lookup:

| Folder type | ERC → id | id → ERC | Primary key getter |
|---|---|---|---|
| `DLFolder` | `DLFolderPersistence.fetchByERC_G` (no `LocalService` convenience method exists) | `DLFolderLocalService.fetchDLFolder` | `getFolderId()` |
| `JournalFolder` | `JournalFolderLocalService.fetchJournalFolderByExternalReferenceCode` | `JournalFolderLocalService.fetchFolder` | `getFolderId()` |
| `KBFolder` | `KBFolderLocalService.fetchKBFolderByExternalReferenceCode` | `KBFolderLocalService.fetchKBFolder` | `getKbFolderId()` |

`FolderResolver` is bidirectional, unlike `DefinitionResolver` — both directions are needed because
Liferay's own stock folder item-selector popups (used by the Root Folder picker) only ever return a
raw numeric id; there's no "pick by ERC" UI to reach for instead. The config action
(`FolderTreePortletConfigurationAction`) resolves that raw id to its ERC **once, at save time**, via
`resolveExternalReferenceCode(folderId, folderEntryClassName)` — the picker's hidden input is named
`rootFolderIdPicked`, deliberately *not* under the `preferences--xxx--` convention, since the raw id
it carries is never itself the persisted value.

The fix reaches further than the preference itself: the breadcrumb's own URL token
(`{type}::{subfolderId}` in the `parameterName` query parameter) carries the same portability risk —
a bookmarked or shared breadcrumb link with a raw folder id would point at the wrong folder (or
nothing) after a re-import, even though the *preference* was already fixed. So `subfolderId` is now
an ERC too: `FolderTreePortletSharedSearchContributor` resolves it to a numeric id before building any
ES query; `FolderTreePortlet` resolves it before walking the parent-folder chain for the breadcrumb,
and resolves each ancestor's *own* numeric id back to an ERC (`resolveExternalReferenceCode`) before
handing it to the view as a `FolderItem` — the walk itself stays on raw numeric ids throughout (an
ERC round-trip per ancestor would be wasteful), only the externally-facing token changes. The same
row-level "navigate into this folder" action for folder-type search results
(`SearchEntryActionsTag`, used by `Display Search Results`) builds the identical token from a row's
own `entryClassPK` — fixed the same way, resolving to that row's ERC before it reaches the URL.

The shared literal `"0"` sentinel (root-level content, `DEFAULT_PARENT_FOLDER_ID`) is preserved as a
special case throughout and never passed to ERC resolution — it isn't a real folder and has no ERC.
If an ERC in a URL or preference doesn't resolve on the current instance (stale bookmark, or content
not yet re-imported here), every call site degrades to "no filter" rather than erroring or filtering
on a value that can never match.

**One exception worth noting, not to copy the same fix onto blindly:** `displayStyleGroupId`
already follows the rule in spirit — Liferay's own Application Display Template picker stores an
ID *and* a key/ERC-like field side by side (`displayStyleGroupKey: "Guest"`, and elsewhere
`displayStyleGroupExternalReferenceCode` paired with an ID). That's Liferay core's own established
pattern for this exact problem, already shared across every ADT-driven widget on the platform —
confirm (by reading the actual lookup code) whether it already falls back to the key/ERC before
assuming it needs the same fix as the project's own custom preferences.

## Applying this rule

**When reviewing or adding a preference on any custom portlet (not just `modules/search`):**
- If the value is, or resolves to, a Liferay primary key referencing another entity → store the
  ERC instead. Resolve ERC → ID via the entity's local service ERC-based fetch method (e.g.
  `DLFolderLocalService`, `DDMStructureLocalService`, `DLFileEntryTypeLocalService` all have or can
  be given ERC-based lookups) at the point the widget actually needs the numeric ID — not once at
  save time.
- If a portlet configuration UI (`*PortletConfigurationAction`/`*ConfigurationDisplayContext`) lets
  an admin pick the referenced entity, the picker should resolve to and store the ERC, not the raw
  ID, from day one for any *new* preference.

**Known, still-not-fixed instances of the violation** (the table above): `subTypeId` (FieldFacet's
sub-type/field-browse picker — distinct from the now-fixed `definitionERC`). This is a real, scoped
Java change to that widget module, following the exact same pattern as the `definitionId`/
`rootFolderId` fixes above (add an ERC-bearing field/preference, resolve via the entity's local
service at the point of use, thread the resolved id through) — don't treat it as a side effect of
unrelated content-import work; it needs its own pass.
