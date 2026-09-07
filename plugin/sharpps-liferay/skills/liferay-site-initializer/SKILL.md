---
name: liferay-site-initializer
description: >
  Use this skill whenever the user wants to create, modify, debug, or understand a Liferay Site
  Initializer — the mechanism that provisions a new Site with pre-built content (pages, web
  content, documents, KB articles, objects, blueprints, taxonomies, fragments, roles, etc.) on
  creation. Trigger for requests like "create a site initializer", "add a site initializer for
  X", "why didn't my journal-articles/object-entries/layouts get imported", "what folders can a
  site initializer import", "how do I reference a document/object/layout I just imported from
  another resource", or any work under a `client-extensions/*-site-initializer/site-initializer/`
  directory or a module implementing `com.liferay.site.initializer.SiteInitializer`. Also trigger
  for "search experiences blueprint" / "sxp-blueprints" import questions, since that's the
  "Blueprints" resource type a site initializer supports.
---

# Liferay Site Initializer Skill

> Source citations below reference `$LIFERAY_PORTAL`, the dynamically-resolved Liferay Portal
> source checkout — see the `liferay-portal-source` skill to resolve/bootstrap it.

A Site Initializer provisions a brand-new Site (or re-runs against an existing one) with a fixed
bundle of content: pages, Web Content, Documents and Media, Knowledge Base articles, Objects,
Search Experiences (SXP) Blueprints, taxonomies, fragments, roles, and more — all declared as
JSON/resource files under a `site-initializer/` folder, no custom Java required for the common
case.

## 1. Two implementation forms — prefer the Client Extension form on 7.4+/Quarterly

| Form | Where | When |
|---|---|---|
| **Client Extension** (`type: siteInitializer`) | `client-extensions/<name>/client-extension.yaml` + `client-extensions/<name>/site-initializer/...` | **Default choice on 7.4+/Quarterly Release workspaces** (per this workspace's `CLAUDE.md`). No Java, no build step — the workspace plugin auto-zips and deploys it. |
| **OSGi module** implementing `SiteInitializer` | A module with `Liferay-Site-Initializer-*` `bnd.bnd` headers, resources under `src/main/resources/site-initializer/` | Only when you need custom Java logic the declarative form can't express. Both forms are read by the **same engine** (`BundleSiteInitializer`), so the resource-folder contract below is identical either way. |

Both forms are processed by
`modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/.../internal/BundleSiteInitializer.java`
in `liferay-portal` — **this file is the single source of truth**. It may be ahead of the
release this workspace runs on, so when in doubt, grep it rather than trust this skill's tables
blindly (Section 6 has the exact greps).

## 2. Minimal `client-extension.yaml`

```yaml
my-site-initializer:
    name: My Site Initializer
    oAuthApplicationHeadlessServer: my-site-initializer-oahs
    siteExternalReferenceCode: MY_SITE
    siteName: My Site
    type: siteInitializer
my-site-initializer-oahs:
    .serviceAddress: localhost:8080
    .serviceScheme: http
    name: My Site Initializer OAuth Application Headless Server
    scopes:
        -   Liferay.Headless.Site.everything
    type: oAuthApplicationHeadlessServer
```

`Liferay.Headless.Site.everything` alone is what Liferay's own official samples use even when
the initializer also imports objects/documents/web content/blueprints (`liferay-sample`,
`liferay-learn`, `liferay-partner-site-initializer-code` in
`liferay-portal/workspaces/*/client-extensions/`) — the engine calls the internal REST resources
in-process as the current user, not via this OAuth app, so extra scopes are normally only needed
if something *else* will call this CX's headless APIs later. Don't copy a huge scope list from a
real-world sample without checking whether your initializer actually needs it.

### `siteExternalReferenceCode` semantics — confirmed by tracing `SiteResourceImpl.putSiteSiteInitializer`

This property is the actual **targeting key**, not just a label for a brand-new site:

- On every deploy, `SiteInitializerClientExtension` (a `BundleTrackerCustomizer`) looks up a Group
  by this ERC. **Found → updates that existing site in place** (re-running upserts everything by
  ERC, doesn't duplicate). **Not found → creates a new site**, using `siteName` as its name.
- This is fully automatic — there is no separate "pick an initializer" UI step for the
  `client-extension.yaml` form; it runs the instant the bundle activates.
- **Never point this at a system-required site** (`L_GUEST`, Global, Control Panel) — see
  Section 9, first entry. New sites and ordinary existing (non-system) sites both work fine.

## 2a. What `type: siteInitializer` actually builds — and why most of it doesn't matter here

Building this CX produces (under `client-extensions/<name>/build/liferay-client-extension-build/`):

```
Dockerfile                                  # FROM liferay/batch:latest — LXC/Cloud packaging
LCP.json                                    # "kind": "Job", LXC orchestration metadata
<name>.client-extension-config.json         # OAuth2 app config (real, gets applied)
site-initializer/site-initializer.json      # {"externalReferenceCode", "name"} from the yaml
site-initializer/site-initializer.zip       # the REAL OSGi-deployable artifact
```

**The `Dockerfile`/`LCP.json` are for Liferay Cloud (LXC)'s build pipeline and are irrelevant on
a self-hosted/plain-Docker instance** (no LXC control plane = nothing ever builds or runs that
image). Don't mistake their presence for "this needs a separate batch container" — on a vanilla
`liferay/dxp` Docker container, the *nested* `site-initializer/site-initializer.zip` inside the
outer CX zip is what actually gets picked up by `AutoDeployScanner`/Felix FileInstall and
processed by the same `BundleSiteInitializer` engine as the OSGi-module form. Confirmed by reading
`docker exec liferay-dev` OSGi console output (`lb <name>` shows the bundle `Active`) and matching
log lines (`BundleSiteInitializer:536 Initializing <site> for group <id>`) after a plain
`cp dist/<name>.zip /path/to/deploy/`.

## 3. Resource folders the engine supports (under `site-initializer/`)

Every entry below is a real key inside `BundleSiteInitializer._createRMap()` — confirmed by
reading the method, not guessed. Folder/file paths are relative to `site-initializer/`.

| Folder / file | Resource type | Notes |
|---|---|---|
| `documents/group/...`, `documents/company/...` | **Documents & Media** | `group` → new site's root D&M folder; `company` → company-wide library. Subdirectory = D&M folder (optional sibling `<dirname>.metadata.json` to set folder name/`viewableBy`); file = document (optional sibling `<filename>.metadata.json` for document metadata, which can include a `documentType` with `contentFields` — see Section 9 for the field-population gotchas). The Document Type itself must already exist (the site initializer can't create one) — see Section 9 for the batch-CX recipe that does. |
| `journal-articles/...json` + matching `.xml` | **Web Content** (Journal Article) | `.json` has `articleId`, `ddmStructureKey`, `name`; `.xml` is the DDM-structure-shaped content body. Use the built-in `BASIC-WEB-CONTENT` structure key to avoid needing a custom `ddm-structures` entry. Subdirectories under here become Structured Content folders — folder metadata is a **sibling** file named `<dirname>.metadata.json` *outside* the directory (same convention as Section 4's KB folders), e.g. `journal-articles/Public.metadata.json` next to `journal-articles/Public/`. Putting it *inside* the directory instead (`journal-articles/Public/Public.metadata.json`) makes the engine silently fail to find it; see Section 9. |
| `knowledge-base-articles/...metadata.json` | **KB Articles** | See Section 4 — folder vs. article is decided by the presence of an `"articleBody"` key, not by directory vs. file. |
| `object-definitions/*.json` | **Object Definitions** ("sample objects") | One object per file. `"scope": "site"` ties it to the site; `"scope": "company"` makes it global. |
| `object-entries/*.object-entries.json` | **Object Entries** (sample data for an object) | `{"objectDefinitionName": "X", "object-entries": [{...}, ...]}`. Looked up by `objectDefinitionName`, not file name. |
| `sxp-blueprints.json` (single file, JSON array) | **Search Experiences (SXP) Blueprints** — this is what "Blueprints" means for a site initializer | Delegated to a **DXP-only** extension point (`OSBSiteInitializer`, `modules/dxp/apps/osb/osb-site-initializer`) — silently **no-ops** if Search Experiences isn't installed/licensed. Don't assume it ran just because no error was logged. |
| `layout-set/public/metadata.json`, `layout-set/private/metadata.json` | Site's public/private **Layout Set** (theme, color scheme) | |
| `layouts/<name>/page.json` + `page-definition.json` | **Pages** | See Section 5. |
| `layout-page-templates/...` | Page/Display Page Templates | Same `page.json`/`page-definition.json` shape as `layouts/`, plus `display-page-template.json` for Display Page Templates bound to an Object/structure. |
| `layout-utility-page-entries/...` | Utility pages (404, 500, login, etc.) | Sibling `default-utility-page-entries.json` maps type → entry name. |
| `fragments/company/...`, `fragments/group/...` | Fragment Collections | Standard fragment-export `.zip` layout, unzipped. |
| `ddm-structures/...`, `ddm-templates/...` | Custom DDM structures/templates for Web Content | Only needed if you don't use a built-in structure key like `BASIC-WEB-CONTENT`. |
| `data-definitions/*.json` | Data Engine forms (App Builder / Forms) | |
| `taxonomy-vocabularies/...` | Taxonomy vocabularies + categories + keywords | |
| `segments-experiences/...`, `segments-entries.json` | Audience targeting | |
| `style-books/...` | Style Books | |
| `roles.json`, `user-accounts.json`, `user-roles.json`, `organizations.json`, `accounts.json`, `accounts-organizations.json`, `account-group-assignments.json` | Users/Roles/Accounts/Orgs | |
| `resource-permissions.json`, `site-settings.json`, `site-navigation-menus.json` | Permissions / site config / nav menus | `resource-permissions.json` sets group/company-scope default grants — confirmed it does **not** retroactively fix per-instance visibility gaps like `StructuredContentFolder`'s; see Section 9. |
| `workflow-definitions/...`, `notification-templates/...`, `list-type-definitions/...` | Workflow / notifications / picklists | |
| `expando-columns.json`, `expando-values.json` | Custom Fields (Expando) | `expando-values.json`'s `classPk` can reference a just-created resource via a token, e.g. `"[#DOCUMENT_FILE_ENTRY_ID:/site-initializer/documents/group/<folder>/<file>#]"` (quotes included — the `"[#...#]"` form unwraps to a raw number; see Section 6). `addExpandoValues` runs near the **end** of the dependency graph, well after `addOrUpdateDocuments`/`addOrUpdateJournalArticles`, so these tokens are always already populated. Prefer a real Document Type (Section 9) over this when the consumer (e.g. a portlet) reads `documentType.contentFields` specifically — Expando values land in a different DTO field (`customFields`) entirely. |
| `asset-list-entries.json`, `asset-link-entries.json` | Asset Publisher collections / related-assets links | |
| `client-extension-entries.json` | Registers other CETs as widgets during init | |
| `plo-entries.json`, `sap-entries.json` | Portal Language Overrides / Service Access Policy | |
| `object-fields/*.json`, `object-folders/*.json`, `object-relationships/*.json` | Extra fields/folders/relationships layered onto an Object after `object-definitions/` | |
| `commerce-*` (catalogs, channels, option categories, order types, inventory warehouses) | Commerce-specific (delegated, only active if Commerce is installed) | |

A flat, un-nested file directly under a folder is valid where the engine's example fixtures show
it (e.g. a KB article straight under `knowledge-base-articles/`, no folder needed) — don't assume
nesting is mandatory just because a real-world sample happens to use it.

## 4. Knowledge Base articles — folder vs. article disambiguation

There is **no separate "kb-folders" directory** — folders and articles live in the same tree and
are told apart by content, recursively:

```
knowledge-base-articles/
├── getting-started.metadata.json          # no "articleBody" key → KB Folder
└── getting-started/                       # dir matches the metadata file's name (minus suffix)
    └── how-to.metadata.json               # has "articleBody" → KB Article, parented to the folder above
        # how-to/                          # (optional) further dir of the same name for replies/children
└── faq.metadata.json                      # has "articleBody", sits at the TOP level →
                                            # KB Article parented directly to the KB root (no folder)
```

Folder metadata: `{"externalReferenceCode": "...", "name": "..."}`.
Article metadata: `{"externalReferenceCode": "...", "title": "...", "articleBody": "..."}`.

## 5. Pages (`layouts/<name>/`)

- `page.json` — layout metadata: `friendlyURL`, `name`/`name_i18n`, `private`, `hidden`,
  `priority`, `type` (`"Content"`, `"Widget"`, `"url"`, `"link_to_layout"`, ...), optional
  `permissions` array (`roleName`/`scope`/`actionIds`). For the public site's home page you can
  reuse `[$PORTAL_PROPERTY:default.guest.public.layout.*$]` tokens instead of hardcoding values
  (see `site-initializer-welcome` in `liferay-portal` for the canonical example).
- `page-definition.json` — Page Builder content tree: `{"pageElement": {"type": "Root",
  "pageElements": [...]}}`. Element `"type"`s: `Fragment`, `Widget`, `Section`/`Row`/`Column`
  (layout grouping), `Collection` + nested `CollectionItem` (renders a list bound to an Object/
  Asset Publisher provider — `collectionConfig.collectionReference.className` plus
  `fieldKey: "ObjectField_<name>"` mappings inside the `CollectionItem`'s fragments).
- **Built-in fragments need no import**: `BASIC_COMPONENT-heading`, `-paragraph`, `-button`,
  `-image`, `-html`, `-video`, `-card`, `-separator`, `-spacer`, `-tabs`, `-dropdown`, `-date`,
  `-slider`, `-social`, `-external-video` are always available by `fragment.key` — reach for a
  real Fragment Collection (`fragments/`) only when these don't cover the need.
- A `Widget` page element looks like:
  ```json
  {"definition": {"widgetInstance": {"widgetName": "com_liferay_..._Portlet", "widgetConfig": {}}}, "type": "Widget"}
  ```
  e.g. `com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet` configured with
  `classNameIds: ["[$CLASS_NAME_ID:com.liferay.journal.model.JournalArticle$]", ...]` to
  dynamically surface imported Web Content/KB articles/etc. on a page.

## 6. Token substitution (`[$TOKEN$]` / `"[#TOKEN#]"` inside any JSON/XML resource)

Confirmed by reading `SiteInitializerUtil` + the `stringUtilReplaceValues.put(...)` calls in
`BundleSiteInitializer` — **grep, don't guess**, since new tokens get added between releases:

```bash
grep -n 'stringUtilReplaceValues.put(' \
  modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/src/main/java/com/liferay/site/initializer/extender/internal/BundleSiteInitializer.java
```

Confirmed tokens as of this check:

| Token | Resolves to |
|---|---|
| `[$GROUP_ID$]`, `[$GROUP_KEY$]`, `[$COMPANY_ID$]`, `[$GROUP_FRIENDLY_URL$]`, `[$PORTAL_URL$]` | The target site's identifiers |
| `[$PORTAL_PROPERTY:<key>$]` | A whitelisted `portal.properties` value (small fixed whitelist — `default.guest.public.layout.*` keys) |
| `[$CLASS_NAME_ID:<fully.qualified.ClassName>$]` | classNameId, for a small fixed set of classes (Blogs/Calendar/DDL/DDM/DLFileEntry/DLFolder/Journal/KBArticle/MBMessage/WikiPage) |
| `[$DOCUMENT_URL:<resourcePath>$]`, `[$DOCUMENT_FILE_ENTRY_ID:<resourcePath>$]`, `[$DOCUMENT_JSON:<resourcePath>$]` | The just-imported document at that exact `site-initializer/...` resource path |
| `[$OBJECT_DEFINITION_CLASS_NAME:<ObjectName>$]`, `[$OBJECT_DEFINITION_ID:<ObjectName>$]`, `[$OBJECT_DEFINITION_PORTLET_ID:<ObjectName>$]` | Resolved from the `name` in `object-definitions/*.json` |
| `[$<ObjectShortName>#<externalReferenceCode>$]` | A specific Object Entry's numeric ID |
| `[$LAYOUT_ID:<Layout Name>$]` | A layout's ID, by its `name_i18n`/`name` |
| `[$DDM_STRUCTURE_ID:<structureKey>$]`, `[$DDM_TEMPLATE_ID:<templateName>$]`, `[$TEMPLATE_ENTRY_ID:<name>$]` | DDM structure/template IDs |
| `[$JOURNAL_ARTICLE_ID:<articleId>$]` | A Journal Article's resource primary key |
| `[$ASSET_LIST_ENTRY_ID:<key>$]`, `[$DOCUMENT_FILE_ENTRY_TYPE_ID:<key>$]` | Asset Publisher list / D&M file-entry-type IDs |
| `[$RELEASE_INFO:<field>$]` | Build/version metadata (`BUILD_NUMBER`, `VERSION`, ...) |

Tokens only resolve if the resource they reference **already ran** in the dependency graph —
e.g. don't reference `[$OBJECT_DEFINITION_CLASS_NAME:X$]` from `sxp-blueprints.json`; that step
has no declared dependency on object definitions, so it can execute first and leave the literal
text unreplaced. When unsure of execution order, check `_createRMap()`'s `_dependsOn(...)` lists
for both resources, or just test it.

## 7. Verifying before claiming a resource type is/isn't supported

Don't answer "site initializers can't import X" from memory — grep the engine and the real
workspace samples first:

```bash
# Full list of resource "steps" the engine knows about, by name:
grep -oP '(?<=R\(\n?\s*")\w+(?=",)' \
  modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/src/main/java/com/liferay/site/initializer/extender/internal/BundleSiteInitializer.java

# A concrete, exhaustive worked example with every resource type (used in Liferay's own
# integration tests for this exact engine — the most authoritative fixture available):
ls modules/apps/site-initializer/site-initializer-extender/site-initializer-extender-test-bundle-1/src/main/resources/site-initializer/

# Real production Client Extension site initializers, for client-extension.yaml conventions
# and to see which resource combinations actually ship together:
ls workspaces/*/client-extensions/*site-initializer*/site-initializer/
```

(All paths above are relative to the `liferay-portal` checkout, not this workspace.)

## 8. Deploying / re-running

- Client Extension form: build with `./gradlew :client-extensions:<name>:clean
  :client-extensions:<name>:build` (find the exact Gradle project path with `./gradlew projects`
  — it's `:client-extensions:<dir-name>`, not the bare directory name). `blade gw deploy`/`gradlew
  clean deploy -Ddeploy.docker.container.id=$(docker ps -lq)` is Liferay's documented one-shot
  build+deploy command; manually `cp dist/<name>.zip` into the deploy mount works identically and
  is what was used throughout this skill's testing.
- A Site Initializer runs the instant its bundle activates (see Section 2a) — there's no
  separate "pick an initializer" step for the CX form once `siteExternalReferenceCode` is set.
  Re-running (redeploy against the same already-initialized site) is generally idempotent
  **except** where noted in Section 9 (`DuplicateObjectRelationshipException`,
  `DuplicateFolderNameException` from ERC mismatches).
- **Verifying a run actually happened — INFO-level logs, not just "no errors":**
  ```bash
  docker logs --since 2m <container> 2>&1 | grep -E "BundleSiteInitializer|ERROR|Exception"
  ```
  A real run prints `Initializing <key> for group <id>`, one `Invoking <step> took <n> ms` line
  per resource type in dependency order, then `Initialized <key> for group <id> in <n> ms`. A
  step that throws aborts the *entire* `initialize()` call (wrapped in `InitializationException`)
  — nothing after the failing step runs, so don't assume partial success. If you see **only**
  `"Processing <name>.zip"` from `AutoDeployScanner` and nothing else, the OSGi bundle install
  itself stalled (see the "stuck deploy" entry in Section 9) — that is not a successful run, even
  though it looks harmless.
- Bounded `docker logs` calls only — `docker logs <container>` with no `--since`/`--tail` can
  hang scanning full history on a long-lived dev container. Always use `--since <Ntime>` or
  `--tail <N>`.
- The OSGi gogo shell is the fastest way to check bundle state directly:
  `docker exec <container> bash -c "(printf 'lb <name>\r\n'; sleep 2; printf 'disconnect\r\n';
  sleep 1) | telnet localhost 11311"` — look for `Active` (or `Resolved`, which is also normal for
  a resource-only bundle with no Activator/DS components; don't read "not Active" as failure by
  itself).

## 9. Known limitations & platform bugs — empirically confirmed, not guessed

Every entry below was reproduced and root-caused against a real `liferay/dxp:7.4.13.nightly`
Docker instance with full stack traces, not inferred from reading source alone. Re-verify against
the actual running version before assuming these still apply on a different build.

**Never target a system-required site (`L_GUEST`, Global, Control Panel) via
`siteExternalReferenceCode`.** Two layered failures, in order:
1. With no `active` field in the generated `site-initializer.json` (the yaml has no property for
   this), `SiteResourceImpl._updateGroup` throws `NullPointerException: ... Site.getActive() is
   null` — it unboxes a `Boolean` that's null whenever the request DTO omits `active`.
2. Patching the payload to include `"active": true` gets past the NPE but then hits
   `RequiredGroupException$MustNotDeleteSystemGroup` from `GroupLocalServiceImpl.updateGroup` —
   Liferay refuses to update core attributes of a system-required group through this path,
   full stop. There is no working fix; **use a new site ERC, or an existing *ordinary* site**
   (re-running against a normal previously-created site works fine — only system sites are
   blocked).

   **If you specifically need to push data into Guest anyway**, see the `liferay-batch-client-extension`
   skill — a `type: batch` Client Extension calls REST resources directly and never touches the
   Group entity, so it isn't subject to this block. Its proven scope is narrower than a Site
   Initializer's, though (Objects/List Types/Workflows/Roles/Users — not pages/documents/web
   content/KB articles), so it isn't a drop-in replacement.

**Object Definitions and Object Relationships are company-scoped, never site-scoped** —
`"scope": "site"` only affects where *entries* live, not the definition/relationship itself. If
you're exporting from/re-importing into the **same company**, an `object-relationships/*.json`
file must reuse the relationship's real, already-existing `externalReferenceCode` (query it via
`/o/object-admin/v1.0/object-definitions/{id}/object-relationships`) — a made-up ERC causes the
ERC-lookup to miss the existing relationship and attempt a second create, which Liferay rejects
with `DuplicateObjectRelationshipException` (relationship `name` must be unique per object,
regardless of ERC). Object Definitions themselves don't have this problem — `addObjectDefinitions`
looks up by `name`, not ERC, so it updates in place correctly either way.

**MultiselectPicklist object-entry values are a plain array of key strings**, e.g.
`["red", "green"]` — *not* `[{"key": "red"}, ...]`. That object-with-`key` shape is only correct
for a single-value **Picklist** field (`{"key": "active"}`). Using the Picklist shape for a
Multiselect field fails with `ObjectEntryValuesException$ListTypeEntry: Object field name "X" is
not mapped to a valid list type entry` — easy to misdiagnose as a missing list-type-entry problem
when it's actually a value-shape problem.

**`KnowledgeBaseArticle` with `"viewableBy": "Anyone"` requires an explicit `"datePublished"`** —
omitting it throws `KBArticleDisplayDateException: Display date is null`. This pairing isn't
documented anywhere obvious; only KB articles set to `Anyone` visibility hit it (Owner-only
articles, the default, don't need a display date).

**`StructuredContentFolder`'s `"viewableBy"` is silently ignored on creation — a genuine platform
gap, not a metadata mistake.** Confirmed via direct comparison: the *identical* pattern (a
`viewableBy: "Anyone"` key in the metadata JSON) correctly grants Guest/Site Member `VIEW` on a
`KnowledgeBaseFolder`/`KnowledgeBaseArticle`, but does nothing for a `StructuredContentFolder` —
it comes back Owner-only regardless. **Tried and confirmed non-working as a fix:** a group-scope
`resource-permissions.json` entry for `com.liferay.journal.model.JournalFolder` (Guest/Site Member
`VIEW`) — `addOrUpdateResourcePermissions` runs without error but doesn't retroactively or
prospectively affect folders created via this headless-resource path. **The only confirmed-working
fix** is calling `PUT .../o/headless-delivery/v1.0/structured-content-folder/{id}/permissions`
directly *after* the folder exists (needs its runtime-assigned ID, so it can't be expressed
declaratively in the static site-initializer files at all) — document this as a required manual
step (Site Settings → the folder's own Permissions action, or that PUT call) rather than chasing
a fix that doesn't exist on this build.

**Headless REST path quirks that cause silent 404s, not engine bugs** — verify the exact path
before assuming a resource lacks an endpoint:
- Single-resource GET/permissions for `StructuredContentFolder` is **singular**:
  `/o/headless-delivery/v1.0/structured-content-folder/{id}` (note: no trailing `s`), while the
  list/create endpoints are plural (`/structured-content-folders`).
- A site-scoped custom Object's entries (`"scope": "site"` in its definition) live at
  `/o/c/<pluralName>/scopes/{groupId}` — the bare `/o/c/<pluralName>` (no `/scopes/{id}`) returns
  HTTP 409 `"Conflict with getObjectEntriesPage"` for these, even though it works fine for
  `"scope": "company"` objects. Find the exact REST path name (it's not always a naive
  pluralization) via the object-definitions list response's `restContextPath` field.
- Deleting a Site is `DELETE /o/headless-admin-site/v1.0/sites/{siteExternalReferenceCode}` — the
  path parameter is the **ERC string**, not the numeric `id`; the numeric-ID form 404s.

**A Structured Content (Web Content) folder's metadata file in the wrong location produces a
misleading `DuplicateFolderNameException`, not a "file not found" error.** `_addOrUpdateStructuredContentFolders`
reads `<parentResourcePath>.metadata.json` — i.e. a file that's a **sibling** of the folder
directory, not nested inside it. Putting it inside instead
(`journal-articles/Public/Public.metadata.json` rather than `journal-articles/Public.metadata.json`)
means the read returns `null`, so the engine silently falls back to `{"name": "<dirname>"}` with
**no `externalReferenceCode` at all**. The resulting ERC-less lookup never matches the
already-existing folder (even when that folder's real ERC is correct and verified independently
via direct REST calls/DB queries — every other check passes, which makes this very confusing to
debug), so it tries to *create* a new folder with the same name and fails with
`DuplicateFolderNameException: <name>` — the error gives no hint that the actual cause is a missing
metadata file. If you hit this and have already confirmed the target folder's ERC matches via a
manual REST call, check the metadata file's *path*, not its *contents*, next. Fix: move the file up
one level so it's a sibling of the directory, matching the same convention KB folders already use
(Section 4).

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
5. Now that the type exists, a document's `<file>.metadata.json` (the *existing*, already-documented
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
`value`) when copying source field definitions per the recipe above.

**Fields that reference *other* entities (an image picker, a structured-content/journal-article
reference) don't have a reliable way to resolve against a freshly-imported target and are best left
unset** rather than faked — there's no stable cross-import ID for "the image that happened to exist
on the source site" without also reproducing that exact document, and guessing wrong fails silently
the same way the `fieldReference` bug does.

**A manually `uninstall`-ed CX bundle can get permanently stuck on redeploy** — if you uninstall
a site-initializer bundle via the OSGi console (e.g. to force a fresh `addingBundle()` re-trigger
for testing), redeploying the *same* zip afterward can silently no-op forever: `AutoDeployScanner`
logs `"Processing <name>.zip"` but the bundle never reappears, even across multiple rebuilds with
different checksums. A `stop`/`start` cycle on an already-installed bundle does **not** re-fire
`addingBundle()` either (only a genuine fresh install does, and the deploy scanner's own tracking
gets confused once you've manually torn down its bundle). **Fix: restart the whole container**
(`docker restart <container>`) — this forces a clean OSGi rescan on boot and reliably recovers.
Avoid manually uninstalling a CX bundle via the OSGi console at all if you can help it; prefer
redeploying a content-different zip and waiting for the directory watcher's natural
stop/start-on-update cycle, which *does* work.
