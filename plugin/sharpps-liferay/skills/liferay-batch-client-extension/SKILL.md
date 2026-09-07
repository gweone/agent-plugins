---
name: liferay-batch-client-extension
description: Use whenever the user wants to create, modify, debug, or understand a Liferay "Batch" Client Extension (`type: batch` in client-extension.yaml, `*.batch-engine-data.json` files under a `batch/` folder) — the mechanism for importing Object Definitions, Object Entries, Object Relationships, List Type Definitions, Workflow Definitions, Roles, or User Accounts via the Headless Batch Engine. Trigger for "create a batch client extension", "import object entries via batch", "batch-engine-data.json format", "how do I target a specific site/scopeKey in a batch import", or any work under a `client-extensions/*-batch/batch/` directory. Also trigger when a Site Initializer can't be used because the target is a system-required site (Guest/Global/Control Panel) — batch client extensions are the workaround. See the companion `liferay-site-initializer` skill for that mechanism and why it's blocked for system sites.
---

# Liferay Batch Client Extension Skill

> Commands below reference `$LIFERAY_PORTAL`, the dynamically-resolved Liferay Portal source
> checkout — see the `liferay-portal-source` skill to resolve/bootstrap it before running them.

A Batch Client Extension imports data by calling existing Headless REST "collection" resources
directly (Object Definitions/Entries, List Types, Workflow Definitions, Roles, Users) — declared
as `*.batch-engine-data.json` files, no custom Java required. It is a **different mechanism**
from a Site Initializer: it never creates or updates a Site/Group entity, it only calls
already-existing REST endpoints scoped to whatever site you tell it to target.

## 1. Why this exists alongside the Site Initializer skill — the Guest-site workaround

The `liferay-site-initializer` skill documents (Section 9) that `siteExternalReferenceCode:
L_GUEST` is permanently blocked: `SiteResourceImpl.putSiteSiteInitializer` →
`GroupLocalServiceImpl.updateGroup` throws `RequiredGroupException$MustNotDeleteSystemGroup`
because that whole code path tries to update the **Group entity itself** (rename/recreate),
which Liferay refuses for the Guest/Global/Control Panel system groups — there is no fix.

A Batch Client Extension sidesteps this entirely: it calls the **same REST resources** (Object
Entries, etc.) the site initializer engine calls internally, but via the generic Headless Batch
Engine, which **never touches the Group entity** — it only looks up the target group's ID to
scope a REST request, the identical lookup ordinary headless API calls already use. Confirmed by
reading `VulcanBatchEngineTaskItemDelegateAdaptor._applyParamConverters` (Section 4) — there is no
`updateGroup` call anywhere in this path.

**Practical implication:** Batch Client Extensions are the right tool when you specifically need
to push data into Guest (or Global/Control Panel) and a Site Initializer is blocked. For an
*ordinary* site (new or existing, non-system), prefer the Site Initializer — it covers far more
resource types (pages, documents, web content, KB articles, blueprints) with declarative file
formats matched to each type, whereas Batch's *proven* scope is narrower (Section 3).

## 2. Minimal `client-extension.yaml`

```yaml
assemble:
    -   from: batch
        into: batch
my-batch:
    name: My Batch
    oAuthApplicationHeadlessServer: my-batch-oahs
    type: batch
my-batch-oahs:
    .serviceAddress: localhost:8080
    .serviceScheme: http
    name: My Batch OAuth Application Headless Server
    scopes:
        -   Liferay.Headless.Batch.Engine.everything
        -   Liferay.Object.Admin.REST.everything
    type: oAuthApplicationHeadlessServer
```

**The `assemble:` block at the top is mandatory and easy to miss — there is no build-time
warning if you omit it.** Confirmed by reproducing the failure end-to-end: without it, the
build still succeeds, `createClientExtensionConfig` still writes
`Liferay-Client-Extension-Batch=batch/` into `WEB-INF/liferay-plugin-package.properties`, but
the **`batch/` folder itself never gets copied into the final dist zip** (verified with
`unzip -l dist/<name>.zip` — only `WEB-INF/`, `Dockerfile`, `LCP.json`, and the CX config JSON
were present, no `batch/`). The deployed bundle's actual manifest then has **no**
`Liferay-Client-Extension-Batch` header at all (verified via `headers <bundleId>` in the OSGi
console) — so `BatchEngineBundleTracker.addingBundle()` returns immediately at its very first
check and does nothing. The result: the bundle installs and goes `Active`, **zero errors or
warnings appear anywhere**, and the import simply never happens. The only way to notice is
`unzip -l` on your own dist zip before deploying, or checking the live bundle's headers after.
Unlike `siteInitializer` (whose `site-initializer/` folder is packaged automatically, confirmed
by its build log showing a dedicated `buildSiteInitializerZip` task), `type: batch` has no
equivalent automatic task — the build log will show `assembleClientExtension NO-SOURCE` and
nothing else copies `batch/` for you.

Confirmed via `client-extension.schema.json` (`gradle-plugins-workspace`): `type: batch` only
requires `oAuthApplicationHeadlessServer` — there is **no `siteExternalReferenceCode`/`siteName`
equivalent at the CX-config level** (unlike `siteInitializer`). The target site is specified
**per batch-engine-data.json file**, via a `parameters` key — see Section 5.

Add OAuth scopes matching whatever resource types you import — `Liferay.Object.Admin.REST.everything`
for Objects, `Liferay.Headless.Admin.Workflow.everything` for workflows, `Liferay.Headless.Admin.User.everything`
for users/roles, etc. (matches the project's own `.claude/rules/cx.md` guidance for batch-type CX scopes.)

## 3. What's actually supported — proven vs. theoretical

**Proven by real usage** — every single `type: batch` example across all of `liferay-portal`'s
`workspaces/*/client-extensions/*-batch/batch/*.json` files (12+ real workspaces checked) uses
only these `className` values:

| `className` | Imports |
|---|---|
| `com.liferay.object.admin.rest.dto.v1_0.ObjectDefinition` | Object Definitions |
| `com.liferay.object.admin.rest.dto.v1_0.ObjectFolder` | Object Folders |
| `com.liferay.object.admin.rest.dto.v1_0.ObjectRelationship` | Object Relationships |
| `com.liferay.object.rest.dto.v1_0.ObjectEntry` | Object Entries (sample/seed data, incl. file **attachments** — see Section 6) |
| `com.liferay.headless.admin.list.type.dto.v1_0.ListTypeDefinition` | Picklist/Multiselect list types |
| `com.liferay.headless.admin.workflow.dto.v1_0.WorkflowDefinition` | Workflow definitions |
| `com.liferay.headless.admin.user.dto.v1_0.Role`, `UserAccount` | Roles, User Accounts |

**Also confirmed proven by live testing (not a real-world sample, but reproduced end-to-end with
zero caveats):**

| `className` | Imports |
|---|---|
| `com.liferay.search.experiences.rest.dto.v1_0.SXPBlueprint` | Search Experiences Blueprints — company-scoped, no `siteId` needed, full `configuration` blob round-trips intact (see the dedicated note further down) |

**Update — `StructuredContent` (Web Content) tested live across 4 attempts: shell creation
works, content body population does not (yet) — three targeted fixes, three failures.** Built a
real test file (`className: com.liferay.headless.delivery.dto.v1_0.StructuredContent`,
`"siteId": "L_GUEST"` in parameters **plus** `"siteId": 20126` — the actual numeric group ID —
on the item itself, since `siteId` is a real `type: integer` field on this DTO, not just a batch
parameter) and deployed it four times, fixing one real, evidenced problem each round:

1. **`contentFields: [{"name": "content", "contentFieldValue": {"data": "<p>...</p>"}}]`** — no
   error, task `COMPLETED`, article shell created on Guest (confirmed: real `id`, correct
   `title`/`externalReferenceCode`, Guest's `structured-contents` count went 0→1 — proves Web
   Content batch import against Guest is real, not just theoretical). **But** `contentFields` came
   back `{"data": ""}` — empty. Root-caused by reading `StructuredContentResourceImpl._toFields`:
   the flat `contentFieldValue` path does `Field field = fields.get(entry.getKey()); if (field ==
   null) continue;` against the *new* article's not-yet-populated `Fields`, silently dropping the
   value when the key isn't already present.
2. **Switched to `contentFieldValue_i18n: {"en_US": "<p>...</p>"}`** (a string), reasoning that
   `_containsI18nMap()` being true routes through a different, more thorough
   `DDMFormValuesUtil.toDDMFormValues(...)` path that builds fields from scratch instead of
   looking one up. Result: a real, different, **schema** error this time —
   `Cannot construct instance of ContentFieldValue ... no String-argument constructor` — so
   `contentFieldValue_i18n` is `Map<String, ContentFieldValue>` (an object per locale), not
   `Map<String, String>`.
3. **Fixed to `contentFieldValue_i18n: {"en_US": {"data": "<p>...</p>"}}`** (proper nested
   object). No error, task `COMPLETED`, new article shell created (fresh `id`, since the first
   was deleted). Content **still** empty.
4. **Hypothesized the locale wasn't registering as "available"** for this item (since
   `DDMFormValuesUtil.toDDMFormValues` takes an `availableLocales` set derived from elsewhere,
   and the item used a plain `"title"` string rather than `"title_i18n"`), so switched to
   `"title_i18n": {"en_US": "..."}`. Result: `availableLanguages` on the created article correctly
   showed `["en-US"]` this time (confirming the hypothesis was *partially* right — title-locale
   handling did change), but `contentFields` was **still** empty.

**Stopped here — diminishing returns.** Three real, evidenced fixes in a row, each one changing
observable behavior (a schema error, then a populated `availableLanguages`), yet the content body
never actually saves. This points to something deeper in how `DDMFormValuesUtil.toDDMFormValues`
or the underlying `JournalArticleService` update call handles a *brand-new* article's DDM field
values specifically via this batch path — not a simple shape mistake left to find. If you need
this working, the next real step is reading `DDMFormValuesUtil.toDDMFormValues` itself line by
line (not guessing at more JSON shapes), or testing whether **`UPDATE`-ing an already-existing**
article (created some other way first, so its `Fields` aren't empty) succeeds where `CREATE`
doesn't — that would confirm/deny the `_toFields` `fields.get(key) == null` theory precisely.

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
Guest too, same reasoning as Section 1) — don't reach for Batch here until you've verified it
actually round-trips the resource type you need.**

**SXP Blueprints are a special case worth calling out separately**: confirmed via
`BaseSXPBlueprintResourceImpl`'s REST paths (`/sxp-blueprints`, `/sxp-blueprints/{id}`, ...) that
they're **company-scoped, with no site/group identity anywhere** — same as Object Definitions.
This means the Section 4 `siteId` targeting trick is irrelevant for blueprints (there's no "which
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
column in Section 3** — this is no longer theoretical.

**Update — `DocumentDataDefinitionType` and `DocumentMetadataSet` (Document Library custom
"Document Types"), tested live, full success.** These are the REST resources behind Documents &
Media's custom Document Types (e.g. a "Metadata Form" type with its own structured fields) — easy
to miss because searching for "DocumentType" literally doesn't find them; the real classes are
`com.liferay.headless.delivery.dto.v1_0.DocumentMetadataSet` (a reusable field set) and
`com.liferay.headless.delivery.dto.v1_0.DocumentDataDefinitionType` (the type itself, which can
have its own fields plus attach metadata sets via `documentMetadataSetIds: [<numeric id>]`). The
Site Initializer engine has **no** creation path for either (see the `liferay-site-initializer`
skill, Section 9) — this is one of the few resource types where Batch is strictly more capable,
not just a Guest-targeting workaround. Recipe, with the two gotchas specific to these two
resources:
1. Capture the real field definitions from the source via `GET .../document-metadata-sets/{id}`
   and `GET .../document-data-definition-types/{id}` and reuse the `dataDefinitionFields` arrays
   verbatim — the shape is intricate (Data-Engine-style `fieldType`/`customProperties`, not the
   older DDM `dataType`/`type` shape Web Content structures use).
2. POST the metadata set first (its own batch file, `"siteId": "<site>"` in parameters). Use
   `"createStrategy": "INSERT"` with **no** `updateStrategy` key — `"UPDATE"` is rejected with
   `Illegal update strategy UPDATE` even though `putSite...ByExternalReferenceCode` exists; the
   generated batch delegate just doesn't register it for this resource. Practical effect:
   redeploying this file a second time throws a benign per-item duplicate-ERC error — treat this
   as a one-time schema bootstrap, not part of a repeatable redeploy cycle.
3. Also required on the item: `"availableLanguages": ["en-US"]`, or the underlying Data Engine
   `DataDefinitionResource` rejects it with `DataDefinitionValidationException$MustSetAvailableLocales`.
4. Deploy, then look up the metadata set's real auto-assigned `id` via REST (can't be predicted) —
   needed for step 5.
5. POST the Document Type as a second batch file, with `"documentMetadataSetIds": [<that id>]` and
   its own `dataDefinitionFields`. Same `INSERT`-only and `availableLanguages` rules apply.

Once the type exists, populating it on a document created via the Site Initializer's normal
`documents/<file>.metadata.json` mechanism works — but only if you key `contentFields` by
`fieldReference`, not `name`; see the `liferay-site-initializer` skill's Section 9 for the exact
failure mode (silently empty values, zero errors) and the `grid`-field value-key gotcha that goes
with it.

## 4. Targeting a specific site — the actual mechanism, verified

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
relationship resolution via `objectDefinitionExternalReferenceCode1`/`2` (Section on Object
Relationships) both worked correctly too. The only thing that stood between "should work per the
source" and "actually works" was the `assemble:` yaml block in Section 2 — once that was in
place, all four `*.batch-engine-data.json` files processed cleanly with zero errors.

## 5. `*.batch-engine-data.json` format

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
      "siteId": "<optional — groupKey | numeric groupId | ERC, see Section 4>"
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
  files, where Multiselect needs a plain string array — see the other skill's Section 9. **Don't
  assume the two engines share a value-shape convention; verify per-engine.**

## 6. Binary attachments on Object Entries

A real, confirmed pattern (`liferay-ticket-workspace/client-extensions/liferay-ticket-batch/batch/`):

```
batch/
├── 03-object-entry.batch-engine-data.json
└── attachments/
    ├── TICKET_1/
    │   └── ticket_1.pdf
    ├── TICKET_2/
    └── TICKET_3/
```

In the JSON, reference the file with a placeholder token plus the real filename:

```json
"attachment": {
    "fileBase64": "@batch_object_entry_file_base64@",
    "name": "ticket_1.pdf"
}
```

The build step substitutes `@batch_object_entry_file_base64@` with the actual file's base64
content, matched by the surrounding `attachments/<externalReferenceCode>/` directory convention.

## 7. Deploying — same OSGi auto-trigger pattern as Site Initializer, same LXC red herring

Confirmed by reading `BatchEngineBundleTracker`
(`modules/apps/batch-engine/batch-engine-service/.../internal/bundle/BatchEngineBundleTracker.java`):
a `BundleTrackerCustomizer` tracking `Bundle.ACTIVE` that checks for the
`Liferay-Client-Extension-Batch` manifest header (set by `CreateClientExtensionConfigTask` when
`type: batch`) and, if present, automatically reads every `*.batch-engine-data.json` in the bundle
via `BatchEngineUnitReader` and runs them through `BatchEngineUnitProcessor` — **fully automatic
on bundle activation**, identical in spirit to `SiteInitializerClientExtension`'s `addingBundle()`.

- **Building it also generates a `Dockerfile`/`LCP.json`** (confirmed by reading
  `CreateClientExtensionConfigTask` directly — `batchType` is set to `"batch"` and both files are
  written unconditionally). **This is still an LXC-only artifact, irrelevant for self-hosted
  Docker** — same conclusion as the Site Initializer skill's Section 2a, for the same reason: the
  manifest header is what the in-process `BatchEngineBundleTracker` actually keys off, not
  anything in those generated files. Don't be misled into thinking a separate `liferay/batch`
  container run is required on a plain `liferay/dxp` container — it isn't, the bundle tracker
  handles it the instant the bundle activates.
- **Re-deploy dedup is per-bundle-`lastModified`, not per-content-hash**: `BatchEngineUnitProcessorImpl._isProcessed()`
  writes a marker file (`bundle.getDataFile(...)`) keyed by the bundle's `lastModified` timestamp.
  Redeploying byte-identical content with a genuinely new build (new `lastModified`) reprocesses;
  redeploying without rebuilding does not. This mirrors the Site Initializer skill's
  AutoDeployScanner dedup caveat — always do a fresh `clean` + `build` before redeploying to test
  a fix, not just `cp` the same already-built zip again.
- Verify a run happened via the same `docker logs --since <Ntime> | grep -E "BatchEngine|ERROR|Exception"`
  approach as the other skill. **The log lines that actually appeared in a real successful run**
  were `BatchEngineImportTaskExecutorImpl:106 Started batch engine import task <id>` and
  `BatchEngineImportTaskExecutorImpl:195 Finished batch engine import task <id> in <n>ms` — one
  pair per `*.batch-engine-data.json` file, in filename order. (`BatchEngineUnitProcessorImpl`'s
  own `"Successfully enqueued/deployed batch file..."` INFO lines exist in source but did not
  appear in practice — don't rely on those specifically; `BatchEngineImportTaskExecutorImpl`'s
  lines are the ones actually observed.) **Total silence (bundle goes `Active`, zero log lines at
  all, not even the AutoDeployScanner's "Processing..." follow-up) is the single biggest red
  flag** — it means `addingBundle()` returned at its very first check, almost always because the
  `Liferay-Client-Extension-Batch` header is missing. Check immediately with:
  ```bash
  unzip -l dist/<name>.zip | grep batch/          # is the batch/ folder even in the artifact?
  # then, after deploying:
  docker exec <container> bash -c "(printf 'headers <bundleId>\r\n'; sleep 2; printf 'disconnect\r\n'; sleep 1) | telnet localhost 11311" | grep Liferay-Client-Extension-Batch
  ```
  Missing from either → you're hitting the missing `assemble:` block from Section 2, not a data
  or filter-matching problem. **Always verify this before debugging anything else** — it was the
  actual root cause the one time this was reproduced, and every plausible-looking alternative
  theory (OSGi service filter mismatches, `taskItemDelegateName` typos, dedup-by-`lastModified`)
  was a dead end until this was checked.
- **Don't trust the data until you check it directly** — a clean Active bundle with zero errors
  is not proof of success (see above). The only conclusive check is querying the actual resource
  afterward and confirming `dateModified` moved to the deploy time.

## 8. Verifying before claiming a resource type is/isn't batch-supported

Don't guess from the `VulcanBatchEngineTaskItemDelegate` interface being implemented (it's
boilerplate on nearly every REST resource) — check **real usage**, not just the interface:

```bash
# Every className actually used across every real-world batch CX sample:
grep -rh '"className"' "$LIFERAY_PORTAL"/workspaces/*/client-extensions/*-batch/batch/*.json | sort -u

# Confirm a specific resource's delegate exists at all (interface implemented ≠ tested/working):
grep -rl "VulcanBatchEngineTaskItemDelegate" "$LIFERAY_PORTAL/modules/apps/<area>/"

# The actual site/scope-targeting logic, if you need to re-verify Section 4 against a newer build:
grep -n "siteId\|scopeKey" "$LIFERAY_PORTAL/modules/apps/portal-vulcan/portal-vulcan-impl/src/main/java/com/liferay/portal/vulcan/internal/batch/engine/VulcanBatchEngineTaskItemDelegateAdaptor.java"
```
