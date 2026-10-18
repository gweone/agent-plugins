# Limitations and nightly-build evidence

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Known limitations & platform bugs — empirically confirmed, not guessed

Every entry below was reproduced and root-caused against a real `liferay/dxp:7.4.13.nightly`
Docker instance with full stack traces, not inferred from reading source alone. Re-verify against
the actual running version before assuming these still apply on a different build.

## System-required sites

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
   Initializer's, though (Objects/List Types/Workflows/Roles/Users, plus live-tested SXP blueprints and
   document schemas — not proven complete pages/documents/web content/KB imports; see
   [batch resource evidence](../../liferay-batch-client-extension/references/resource-support.md)), so it isn't a drop-in replacement.

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
([KB folder convention](resources.md#knowledge-base-articles--folder-vs-article-disambiguation)).
