---
name: liferay-widget-config-erc
description: >
  Use this skill whenever designing or reviewing ANY portlet/widget configuration (portlet
  preferences, widget config in a `page-definition.json`, a custom `*PortletInstanceConfiguration`)
  in this workspace that references another Liferay entity — a site/group, DDM structure, file
  entry type, D&M folder, taxonomy vocabulary, object definition, layout, etc. Trigger for "add a
  preference that points to X", "how should this widget reference a site/structure/folder", "the
  widget broke after import/staging/LAR", "shows nothing on the new site", or any code review of
  a `*PortletPreferences`/`*ConfigurationAction`/`*DisplayContext` class. This is a general
  engineering rule for this workspace, not limited to any one module — it applies equally to the
  existing `org_sharpps_search_*` portlets (`modules/search`) and to any new custom portlet
  written later.
---

# General Rule: Liferay Widget Configuration Must Store ERC, Never a Raw Numeric ID

## The rule

**Whenever a portlet preference / widget configuration field references another Liferay entity,
store its `externalReferenceCode`, not its numeric primary key.** Resolve the ERC to whatever ID
the current instance actually needs at the point of use (each request, or cached with
invalidation) — never persist a resolved numeric ID back into the configuration.

Numeric Liferay primary keys (`groupId`, `structureId`, `fileEntryTypeId`, `folderId`, ...) are
auto-incremented per database and are **never guaranteed to match** across two different
creations of "the same" entity — including the *same* content recreated on a *different* site or
instance via Site Initializer, Batch, Staging publish, or LAR import. An ERC, by contrast, is
something the implementer chooses and that stays stable across exactly those operations, *provided
it's set explicitly and reused* (which is exactly what this project already does for every Object,
KB article, DDM structure, etc. created via the Site Initializer / Batch Client Extension — see
the `liferay-site-initializer` and `liferay-batch-client-extension` skills). A configuration field
that skips this and stores a raw ID throws away that portability for no benefit — IDs and ERCs are
equally easy to store; only one of them survives a re-import.

## Confirmed evidence this isn't theoretical

Found while reviewing
`page-definition.json` (`client-extensions/sharpps-site-initializer/site-initializer/layouts/search-documentation/document-list/page-definition.json`),
which configures several `org_sharpps_search_*` portlets (`modules/search`,
`org.sharpps.search.*`). Every value below is copied verbatim from the file, straight from the
*source* instance at export time:

| Preference | Found in | Points to | Confirmed in source | Status |
|---|---|---|---|---|
| `rootFolderId: "47866"` | `org_sharpps_search_filter_foldertree_FolderTreePortlet` | A specific `DLFolder` ("documents") | was used **raw**, as `.value(rootFolderId)` in an Elasticsearch term query and in a `treePath` wildcard match; same raw-id pattern in the breadcrumb's own URL token (`{type}::{subfolderId}`) | **Fixed** — see below |
| `definitionId: "44180"`, nested `definitionId` values inside the `displayViews` JSON blob | `org_sharpps_search_facet_field_FieldFacetPortlet`, `org_sharpps_search_filter_field_FieldFilterPortlet`, `org_sharpps_search_results_display_DisplaySearchResultsPortlet` | A specific `DDMStructure` ("Shared Metadata") | was read as `long`, concatenated **into the indexed field name itself**: `"ddm__" + indexType + "__" + definitionId + "__" + fieldReference` | **Fixed** — see below |
| `subTypeId: "44228"` | `org_sharpps_search_facet_field_FieldFacetPortlet` | A specific `DLFileEntryType` ("Metadata Form") | `FieldFacetPortletPreferences.java:22` (`modules/search/src/main/java/org/sharpps/search/facet/field/portlet/FieldFacetPortletPreferences.java#L22`) — deliberately kept separate from `definitionId` per the comment there (different ID space: fileEntryTypeId vs. ddmStructureId) | **Not yet fixed** |
| `displayStyleGroupId: "20126"` | Most widgets on the page (search bar, both facets, display-search-results, folder tree) | A specific Site/Group (Guest, on the source instance) | Standard Liferay ADT picker pattern | **Lower risk**, see below — don't fix the same way |

## `definitionId` → `definitionERC`: fixed, full recipe

Renamed throughout `modules/search`: `DisplayField`/`AssetTypeDescriptor.FieldDescriptor` now carry
a `definitionERC` (`String`) instead of `definitionId` (`long`); `FieldFacetPortletPreferences`/
`FieldFilterPortletPreferences` persist `PREFERENCE_KEY_DEFINITION_ERC` (`"definitionERC"`) instead
of `PREFERENCE_KEY_DEFINITION_ID`; both field-picker JSPs
(`facet/field/configuration.jsp`/`filter/field/configuration.jsp`) emit `data-definition-erc` and a
`definitionERC` hidden input instead of `data-definition-id`/`definitionId`.

A new `org.sharpps.search.definition.DefinitionResolver` OSGi service
(`DefinitionResolver.java` (`modules/search/src/main/java/org/sharpps/search/definition/DefinitionResolver.java`),
`DefinitionResolverImpl.java` (`modules/search/src/main/java/org/sharpps/search/definition/internal/DefinitionResolverImpl.java`))
resolves `(externalReferenceCode, groupId, className)` → the current `DDMStructure.structureId` via
`DDMStructureLocalService.fetchStructureByExternalReferenceCode`, caching the result as an
`HttpServletRequest` attribute keyed by `groupId#className#erc` so multiple widgets/fields on the
same page render don't each re-hit the database. `DisplayField`/`FieldDescriptor` stay plain
data-carrier POJOs with no service dependencies — `buildIndexedFieldName` now takes the
already-resolved numeric id as a parameter (`buildIndexedFieldName(long resolvedDefinitionId[,
String locale])`) rather than resolving it internally, so every caller (the two
`*PortletSharedSearchContributor`s, `DocumentFieldResolver`, and the three places that construct
`DocumentFieldResolver` — `ExportSearchResultsMVCResourceCommand`,
`DocumentFieldResolverTemplateContextContributor`, `SearchEntryFieldTag`) had to thread
`groupId`/`HttpServletRequest` through to the point of use. `getTokenId()` (used for URL filter
tokens) uses the ERC string directly as its disambiguator — no resolution needed there at all, since
any stable per-structure string works equally well for that purpose.

Why this isn't hypothetical: `rootFolderId`/`definitionId`/`subTypeId` are auto-incremented primary
keys, never the same across two different `addStructure`/`addFolder`/`addFileEntryType` calls, even
for conceptually identical content. Confirmed directly in this project: the source Guest site's
"Shared Metadata" structure was `structureId=44180`; recreating the *same* content (same
`externalReferenceCode`, deliberately) on the SharpPS site produced `structureId=61731` — a
completely different number (see the `liferay-site-initializer` skill, Section 9). For
`definitionId` the breakage compounds further: Elasticsearch indexes each DDM field under a name
containing the structure ID (`ddm__keyword__44180__SelectMultiple`); after a fresh import,
re-indexed documents get `ddm__keyword__61731__SelectMultiple` instead, so a facet preference still
holding `"44180"` aggregates on a field name no document has — silently zero results, nothing to
log.

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
