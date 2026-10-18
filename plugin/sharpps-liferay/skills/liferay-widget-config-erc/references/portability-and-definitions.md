# ERC portability and DDM definition migration

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
completely different number (see [Document Type recreation evidence](../../liferay-document-types/SKILL.md)). For
`definitionId` the breakage compounds further: Elasticsearch indexes each DDM field under a name
containing the structure ID (`ddm__keyword__44180__SelectMultiple`); after a fresh import,
re-indexed documents get `ddm__keyword__61731__SelectMultiple` instead, so a facet preference still
holding `"44180"` aggregates on a field name no document has — silently zero results, nothing to
log.
