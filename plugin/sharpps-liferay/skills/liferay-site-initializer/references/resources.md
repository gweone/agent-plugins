# Resource folder contract

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Resource folders the engine supports (under `site-initializer/`)

Every entry below is a real key inside `BundleSiteInitializer._createRMap()` — confirmed by
reading the method, not guessed. Folder/file paths are relative to `site-initializer/`.

| Folder / file | Resource type | Notes |
|---|---|---|
| `documents/group/...`, `documents/company/...` | **Documents & Media** | `group` → new site's root D&M folder; `company` → company-wide library. Subdirectory = D&M folder (optional sibling `<dirname>.metadata.json` to set folder name/`viewableBy`); file = document (optional sibling `<filename>.metadata.json` for document metadata, which can include a `documentType` with `contentFields` — see [document values](../../liferay-document-types/references/document-values.md) for the field-population gotchas). The Document Type itself must already exist (the site initializer can't create one) — see [document schema bootstrap](../../liferay-document-types/references/schema-bootstrap.md) for the batch-CX recipe that does. |
| `journal-articles/...json` + matching `.xml` | **Web Content** (Journal Article) | `.json` has `articleId`, `ddmStructureKey`, `name`; `.xml` is the DDM-structure-shaped content body. Use the built-in `BASIC-WEB-CONTENT` structure key to avoid needing a custom `ddm-structures` entry. Subdirectories under here become Structured Content folders — folder metadata is a **sibling** file named `<dirname>.metadata.json` *outside* the directory (same convention as [KB folders](resources.md#knowledge-base-articles--folder-vs-article-disambiguation)), e.g. `journal-articles/Public.metadata.json` next to `journal-articles/Public/`. Putting it *inside* the directory instead (`journal-articles/Public/Public.metadata.json`) makes the engine silently fail to find it; see [limitations](limitations.md). |
| `knowledge-base-articles/...metadata.json` | **KB Articles** | See [Knowledge Base resources](resources.md#knowledge-base-articles--folder-vs-article-disambiguation) — folder vs. article is decided by the presence of an `"articleBody"` key, not by directory vs. file. |
| `object-definitions/*.json` | **Object Definitions** ("sample objects") | One object per file. `"scope": "site"` ties it to the site; `"scope": "company"` makes it global. |
| `object-entries/*.object-entries.json` | **Object Entries** (sample data for an object) | `{"objectDefinitionName": "X", "object-entries": [{...}, ...]}`. Looked up by `objectDefinitionName`, not file name. |
| `sxp-blueprints.json` (single file, JSON array) | **Search Experiences (SXP) Blueprints** — this is what "Blueprints" means for a site initializer | Delegated to a **DXP-only** extension point (`OSBSiteInitializer`, `modules/dxp/apps/osb/osb-site-initializer`) — silently **no-ops** if Search Experiences isn't installed/licensed. Don't assume it ran just because no error was logged. |
| `layout-set/public/metadata.json`, `layout-set/private/metadata.json` | Site's public/private **Layout Set** (theme, color scheme) | |
| `layouts/<name>/page.json` + `page-definition.json` | **Pages** | See [pages](resources.md#pages-layoutsname). |
| `layout-page-templates/...` | Page/Display Page Templates | Same `page.json`/`page-definition.json` shape as `layouts/`, plus `display-page-template.json` for Display Page Templates bound to an Object/structure. |
| `layout-utility-page-entries/...` | Utility pages (404, 500, login, etc.) | Sibling `default-utility-page-entries.json` maps type → entry name. |
| `fragments/company/...`, `fragments/group/...` | Fragment Collections | Standard fragment-export `.zip` layout, unzipped. |
| `ddm-structures/...`, `ddm-templates/...` | Custom DDM structures/templates for Web Content | Only needed if you don't use a built-in structure key like `BASIC-WEB-CONTENT`. |
| `data-definitions/*.json` | Data Engine forms (App Builder / Forms) | |
| `taxonomy-vocabularies/...` | Taxonomy vocabularies + categories + keywords | |
| `segments-experiences/...`, `segments-entries.json` | Audience targeting | |
| `style-books/...` | Style Books | |
| `roles.json`, `user-accounts.json`, `user-roles.json`, `organizations.json`, `accounts.json`, `accounts-organizations.json`, `account-group-assignments.json` | Users/Roles/Accounts/Orgs | |
| `resource-permissions.json`, `site-settings.json`, `site-navigation-menus.json` | Permissions / site config / nav menus | `resource-permissions.json` sets group/company-scope default grants — confirmed it does **not** retroactively fix per-instance visibility gaps like `StructuredContentFolder`'s; see [limitations](limitations.md). |
| `workflow-definitions/...`, `notification-templates/...`, `list-type-definitions/...` | Workflow / notifications / picklists | |
| `expando-columns.json`, `expando-values.json` | Custom Fields (Expando) | `expando-values.json`'s `classPk` can reference a just-created resource via a token, e.g. `"[#DOCUMENT_FILE_ENTRY_ID:/site-initializer/documents/group/<folder>/<file>#]"` (quotes included — the `"[#...#]"` form unwraps to a raw number; see [tokens](tokens-and-source-verification.md)). `addExpandoValues` runs near the **end** of the dependency graph, well after `addOrUpdateDocuments`/`addOrUpdateJournalArticles`, so these tokens are always already populated. Prefer a real Document Type ([document types](../../liferay-document-types/SKILL.md)) over this when the consumer (e.g. a portlet) reads `documentType.contentFields` specifically — Expando values land in a different DTO field (`customFields`) entirely. |
| `asset-list-entries.json`, `asset-link-entries.json` | Asset Publisher collections / related-assets links | |
| `client-extension-entries.json` | Registers other CETs as widgets during init | |
| `plo-entries.json`, `sap-entries.json` | Portal Language Overrides / Service Access Policy | |
| `object-fields/*.json`, `object-folders/*.json`, `object-relationships/*.json` | Extra fields/folders/relationships layered onto an Object after `object-definitions/` | |
| `commerce-*` (catalogs, channels, option categories, order types, inventory warehouses) | Commerce-specific (delegated, only active if Commerce is installed) | |

A flat, un-nested file directly under a folder is valid where the engine's example fixtures show
it (e.g. a KB article straight under `knowledge-base-articles/`, no folder needed) — don't assume
nesting is mandatory just because a real-world sample happens to use it.

## Knowledge Base articles — folder vs. article disambiguation

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

## Pages (`layouts/<name>/`)

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
