# Resource support and evidence

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## What's actually supported — proven vs. theoretical

**Proven by real usage** — every single `type: batch` example across all of `liferay-portal`'s
`workspaces/*/client-extensions/*-batch/batch/*.json` files (12+ real workspaces checked) uses
only these `className` values:

| `className` | Imports |
|---|---|
| `com.liferay.object.admin.rest.dto.v1_0.ObjectDefinition` | Object Definitions |
| `com.liferay.object.admin.rest.dto.v1_0.ObjectFolder` | Object Folders |
| `com.liferay.object.admin.rest.dto.v1_0.ObjectRelationship` | Object Relationships |
| `com.liferay.object.rest.dto.v1_0.ObjectEntry` | Object Entries (sample/seed data, incl. file **attachments** — see [binary attachments](attachments.md)) |
| `com.liferay.headless.admin.list.type.dto.v1_0.ListTypeDefinition` | Picklist/Multiselect list types |
| `com.liferay.headless.admin.workflow.dto.v1_0.WorkflowDefinition` | Workflow definitions |
| `com.liferay.headless.admin.user.dto.v1_0.Role`, `UserAccount` | Roles, User Accounts |

**Also confirmed proven by live testing (not a real-world sample, but reproduced end-to-end with
zero caveats):**

| `className` | Imports |
|---|---|
| `com.liferay.search.experiences.rest.dto.v1_0.SXPBlueprint` | Search Experiences Blueprints — company-scoped, no `siteId` needed, full `configuration` blob round-trips intact (see the dedicated note further down) |

## Document schema resources

`com.liferay.headless.delivery.dto.v1_0.DocumentMetadataSet` and `com.liferay.headless.delivery.dto.v1_0.DocumentDataDefinitionType` were also live-tested successfully. These create document schemas, not document binaries. The shared [schema bootstrap and value-import workflow](../../liferay-document-types/SKILL.md) is canonical; it includes INSERT-only constraints, duplicate semantics, language requirements, numeric metadata-set ID resolution, and sidecar examples.

## Structured Content investigation

Shell creation is proven; content-body population remained empty after four live attempts. Read the [full investigation and exact shapes](structured-content-investigation.md) before relying on this path.

**Technically wired but with zero real-world usage found — don't assume it works without
testing it yourself first:** the generated `Base*ResourceImpl` class for essentially *every*
Vulcan headless REST resource implements `VulcanBatchEngineTaskItemDelegate` as boilerplate,
including `BaseDocumentResourceImpl`, `BaseKnowledgeBaseArticleResourceImpl`, and
`BaseSitePageResourceImpl` (Pages) — the same boilerplate `SXPBlueprint` had, before it was
tested live and confirmed working (see above). Treat these the same way: plausible, unverified,
worth testing before relying on. Don't be misled by the
generated `OSGI-INF/liferay/rest/v1_0/<resource>.properties` file either — it sets
`batch.engine.task.item.delegate=true`/`batch.planner.import.enabled=true` **identically for every
Vulcan resource**, proven ones included (verified: `object-definition.properties` has the exact
same lines as `sxp-blueprint.properties`/`document.properties`). That file confirms the wiring
exists, which the Java interface already told you — it is not a signal of real-world testedness.
The interface being implemented does not mean the resource was designed/tested for batch import —
a generic JSON-oriented batch file has no obvious way to carry a Document's binary content or a
Page's deeply nested `pageDefinition` tree the way the Site Initializer engine's dedicated,
type-specific handling does (Web Content above is the cautionary example: the shell imports fine,
the actual content body doesn't, yet). **For Documents, KB Articles, and Pages, prefer either the
Site
Initializer (non-system sites) or direct REST calls scoped to the target groupId (works against
Guest too, same reasoning as [Guest-site rationale](packaging.md#why-this-exists-alongside-the-site-initializer-skill--the-guest-site-workaround)) — don't reach for Batch here until you've verified it
actually round-trips the resource type you need.**

**SXP Blueprints are a special case worth calling out separately**: confirmed via
`BaseSXPBlueprintResourceImpl`'s REST paths (`/sxp-blueprints`, `/sxp-blueprints/{id}`, ...) that
they're **company-scoped, with no site/group identity anywhere** — same as Object Definitions.
This means the [siteId targeting](site-targeting-and-format.md) trick is irrelevant for blueprints (there's no "which
site" question), but it also means Batch buys nothing extra here: the Site Initializer's own
`addOrUpdateSXPBlueprint` step doesn't touch the Group entity either, so blueprints were never
actually blocked by the Guest issue *directly* — what blocks them is that
`SiteInitializerClientExtension._addOrUpdateSite()` (the find-or-create-the-Group step) throws
*before* `initialize()` is ever called, aborting the entire run — including the blueprint step —
before it starts. Since blueprints need no Group at all, the simplest fix when only blueprints
are blocked by a Guest-targeting Site Initializer is neither Batch nor a workaround CX — it's a
plain `PUT /o/search-experiences-rest/v1.0/sxp-blueprints/{id}` (upsert by
`externalReferenceCode`, same as any ordinary headless call) reusing the same exported
`sxp-blueprints.json` content.

**Update — tested live, full success, no caveats.** Built a real test file
(`className: com.liferay.search.experiences.rest.dto.v1_0.SXPBlueprint`, no `siteId` needed —
company-scoped, confirmed above) and deployed it. Result: a real blueprint was created (`id`
assigned, correct `title`/`externalReferenceCode`), **and critically the entire nested
`configuration` object — `generalConfiguration`, `queryConfiguration`, etc. — round-tripped
intact**, unlike `StructuredContent`'s `contentFields`. The difference: an SXP Blueprint's
`configuration` is stored as one opaque JSON blob, not mapped field-by-field into a DDM form the
way Web Content is — there's no `fields.get(key) == null` failure mode for it to hit. **SXP
Blueprints can be added to `ObjectDefinition`/`ObjectRelationship`/`ObjectEntry`'s "proven"
column in [resource evidence](resource-support.md)** — this is no longer theoretical.

## Verifying before claiming a resource type is/isn't batch-supported

Don't guess from the `VulcanBatchEngineTaskItemDelegate` interface being implemented (it's
boilerplate on nearly every REST resource) — check **real usage**, not just the interface:

```bash
# Every className actually used across every real-world batch CX sample:
grep -rh '"className"' "$LIFERAY_PORTAL"/workspaces/*/client-extensions/*-batch/batch/*.json | sort -u

# Confirm a specific resource's delegate exists at all (interface implemented ≠ tested/working):
grep -rl "VulcanBatchEngineTaskItemDelegate" "$LIFERAY_PORTAL/modules/apps/<area>/"

# The actual site/scope-targeting logic, if you need to re-verify [site targeting](site-targeting-and-format.md) against a newer build:
grep -n "siteId\|scopeKey" "$LIFERAY_PORTAL/modules/apps/portal-vulcan/portal-vulcan-impl/src/main/java/com/liferay/portal/vulcan/internal/batch/engine/VulcanBatchEngineTaskItemDelegateAdaptor.java"
```
