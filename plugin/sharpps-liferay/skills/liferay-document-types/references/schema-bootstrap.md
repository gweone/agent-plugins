# Document metadata sets and Document Type schemas

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

The original initializer evidence was reproduced on `liferay/dxp:7.4.13.nightly`; the batch notes also report live end-to-end success. Re-verify delegate capabilities against the actual release; PUT-by-ERC support does not establish batch UPDATE support. Deployment requires explicit authorization.

**A Site Initializer cannot create a custom Document Type (`DLFileEntryType`) — but a `type: batch`
Client Extension *can*, fully declaratively, no custom Java required. An earlier version of this
note wrongly concluded no REST resource exists for this — it does, just under a non-obvious name.**
`BundleSiteInitializer` itself has no creation path: the only `DLFileEntryType` reference in the
whole class
(`BundleSiteInitializer.java:789-796` (`$LIFERAY_PORTAL/modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/src/main/java/com/liferay/site/initializer/extender/internal/BundleSiteInitializer.java#L789-L796`))
is a token map built from **already-existing** types for `asset-list-entries.json` filters, and
`ddm-structures/` is hardcoded to `JournalArticle`'s classNameId. But searching for "DocumentType"
literally misses the real resources — they're named **`DocumentDataDefinitionType`** (the type
itself) and **`DocumentMetadataSet`** (the reusable field-set a type can attach), both full REST
resources with `postSite...`/`putSite...ByExternalReferenceCode` methods
(`DocumentDataDefinitionTypeResource.java` (`$LIFERAY_PORTAL/modules/apps/headless/headless-delivery/headless-delivery-api/src/main/java/com/liferay/headless/delivery/resource/v1_0/DocumentDataDefinitionTypeResource.java`),
`DocumentMetadataSetResource.java` (`$LIFERAY_PORTAL/modules/apps/headless/headless-delivery/headless-delivery-api/src/main/java/com/liferay/headless/delivery/resource/v1_0/DocumentMetadataSetResource.java`)).
Internally a Document Type is backed by the Data Engine (App Builder forms) — `DLFileEntryType` now
has a `dataDefinitionId` column alongside the legacy `DDMStructureLink` row.

## Metadata-first schema bootstrap

**The recipe, confirmed working end-to-end against a real instance:**
1. `GET /o/headless-delivery/v1.0/document-metadata-sets/{id}` and
   `GET /o/headless-delivery/v1.0/document-data-definition-types/{id}` on the **source** site to
   capture the exact `dataDefinitionFields` arrays (one call each) — reuse them verbatim rather than
   hand-authoring field JSON; the shape (`fieldType`, `customProperties`, `defaultValue`, etc.) is
   intricate and easy to get subtly wrong by guessing.
2. POST the metadata set first, as its own batch file
   (`className: com.liferay.headless.delivery.dto.v1_0.DocumentMetadataSet`,
   `"siteId": "<site ERC>"` in `configuration.parameters`). Two gotchas specific to this resource:
   - `"updateStrategy": "UPDATE"` is rejected with `Illegal update strategy UPDATE` even though the
     PUT-by-ERC method exists — the generated batch delegate doesn't register it for this resource.
     Use `"createStrategy": "INSERT"` and omit `updateStrategy` entirely. Practical consequence:
     redeploying this file a second time throws a benign `DuplicateDDMStructureExternalReferenceCodeException`
     for that one item — harmless (other files in the same batch run are unaffected), but means this
     step isn't cleanly idempotent; treat it as a one-time schema bootstrap, not part of the
     repeatable redeploy cycle.
   - The underlying Data Engine `DataDefinitionResource` requires `"availableLanguages": ["en-US"]`
     to be set explicitly on the item, or it fails with
     `DataDefinitionValidationException$MustSetAvailableLocales`.
3. Deploy, then query the new metadata set's real numeric `id` via REST (it's auto-assigned, can't
   be predicted) — e.g. `GET /o/headless-delivery/v1.0/sites/{siteId}/document-metadata-sets`.
4. POST the Document Type as a second batch file
   (`className: com.liferay.headless.delivery.dto.v1_0.DocumentDataDefinitionType`), with
   `"documentMetadataSetIds": [<the id from step 3>]` plus its own `dataDefinitionFields` (a type
   can have fields of its own in addition to ones inherited from attached metadata sets — the
   source site's "Metadata Form" had 5 of its own, e.g. Name/Color, plus 11 from a shared
   "Shared Metadata" set, 16 total). Same `INSERT`-only and `availableLanguages` requirements apply.

The exported `dataDefinitionFields` use Data-Engine-style `fieldType`/`customProperties`, not the older DDM `dataType`/`type` shape used by Web Content structures. This distinction and the same two-resource recipe were also recorded in the original batch skill; this is their canonical shared location.
