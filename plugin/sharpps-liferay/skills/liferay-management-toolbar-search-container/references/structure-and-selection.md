# Toolbar structure and authoritative selection state

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

## 0. The one-sentence version

**"Select all" in this taglib combo is never a submitted form field — it's client-side UI state
on an AUI component instance, and reading it requires `Liferay.componentReady(searchContainerId)`,
not DOM inspection.** Nearly every bug in this area traces back to code that tried to read
selection state from the DOM (a checkbox's `.checked`, a `name` attribute that doesn't exist,
`document.querySelectorAll(...)`) instead of from that component.

---

## 1. Architecture: what's server-rendered vs. what's React

```jsp
<%-- Toolbar: React-rendered (ManagementToolbar.js), including the header
     "select all" checkbox and any actionDropdownItems --%>
<clay:management-toolbar
    actionDropdownItems="<%= bulkActions %>"
    searchContainerId="myListSearchContainer"
    selectable="<%= true %>"
    showSearch="<%= true %>"
    itemsTotal="<%= results.size() %>"
/>

<%-- Form + search container: classic server-rendered JSP taglibs --%>
<aui:form action="<%= bulkActionURL %>" method="post" name="fmBulkAction">
    <liferay-ui:search-container id="myListSearchContainer" searchContainer="<%= searchContainer %>">
        <liferay-ui:search-container-row ...>
            <%-- RowChecker renders each row's checkbox: --%>
            <%-- <input name="<ns>rowIds" type="checkbox" value="..." onclick="Liferay.Util.checkAllBox(...)"> --%>
        </liferay-ui:search-container-row>
        <liferay-ui:search-iterator markupView="lexicon" />
    </liferay-ui:search-container>
</aui:form>
```

- `<clay:management-toolbar>` is backed by one React root (`ManagementToolbar.js`, hydrated via
  `getHydratedModuleName()` → `"{ManagementToolbar} from frontend-taglib-clay"`). It renders the
  header "select all" checkbox **and** `<SelectionControls>` as direct children of that same tree
  — confirmed by reading `ManagementToolbar.js:135-163`. Any `actionDropdownItems` (the bulk
  action button/dropdown) are also part of this React tree.
- `<liferay-ui:search-container>` + `RowChecker` are classic, fully server-rendered — every row
  checkbox is real HTML in the initial response, no hydration involved.
- Both are tied together **only** by `searchContainerId` — a shared AUI component instance
  registered under that id (see [the selection API below](structure-and-selection.md)), not by any parent/child DOM relationship.

### Structural rule: render the toolbar OUTSIDE the form

If `showSearch="true"`, the toolbar renders its **own nested inner `<form>`** for the search box.
If the toolbar tag is placed *inside* `<aui:form name="fmBulkAction">`, that inner form ends up
nested inside the outer one — invalid HTML, and the browser's parser response to that is
undefined/inconsistent: row checkboxes can end up **not** associated with the outer form at all
(reported symptom: individually-checked rows silently missing from the submitted payload, or the
bulk-action button doing nothing).

**Fix: always render `<clay:management-toolbar>` before/outside `<aui:form>` opens**, even though
this differs from where you might intuitively place it:

```jsp
<clay:management-toolbar ... />        <%-- outside --%>

<aui:form action="..." name="fmBulkAction">
    <liferay-ui:search-container ...>...</liferay-ui:search-container>
</aui:form>
```

Confirmed as the correct pattern by reading stock Liferay's own admin JSPs (e.g.
`asset-categories-admin-web`'s `view_asset_categories.jsp`, `wiki-web`'s `view_pages.jsp`,
`fragment-web`'s `view_fragment_entries.jsp` — all place the toolbar outside the form). Doing this
also means every server-rendered element inside the form (hidden fields, the submit button, the
search-container's checkboxes) becomes a genuine, plain DOM descendant of that form — no manual
JS checkbox-collection/reattachment hacks are needed for the "normal" (non-select-all) case; a
plain `form.submit()` or a real `type="submit"` button just works.

---

## 2. The "select all" trap (read this before touching anything else)

### What you'd expect

Click the header checkbox → every row matching the current filter gets included in the bulk
action, even ones on other pages, even if there are 500 of them.

### What actually happens OOTB

1. `RowChecker.getAllRowsCheckbox()` (the *legacy* mechanism, `portal-kernel`) is effectively
   dead code in modern Liferay — confirmed by portal-wide grep, its only caller is one deprecated
   JSP. **Don't reach for it.**
2. The real header checkbox — the one you actually see, showing "X of Y Items Selected" — is
   rendered by the toolbar's React tree and **has no `name`/`value` attribute at all.** It's pure
   client-side UI state. It never gets submitted with the form on its own.
3. Its click handler ultimately calls `toggleAllRows()` on the shared AUI component ([selection API below](structure-and-selection.md)),
   which sets `bulkSelection = true` **and** checks every row checkbox physically rendered on the
   **current page only** — confirmed via a live captured request: with 76 total matching items
   and the default 20-row page, "select all" produced a submitted `rowIds` list of exactly
   `n:0..n:19` (20 entries), despite the toolbar label reading "76 of 76 Items Selected."
4. That label is accurate about the *intent* (bulkSelection=true), but **not** about what's
   physically in the DOM to submit — rows on other pages were never rendered, so they can never
   be checked, no matter what the label claims.

**Conclusion: don't trust the DOM for "was select-all used" or "what's selected."** The label can
say one thing while the actually-submittable checkboxes say another. The DOM only ever reflects
the current page.

---

## 3. The real source of truth: `search_container_select.js`

`frontend-js-aui-web/.../liferay/search_container_select.js` is an `A.Plugin.Base` (→ `A.Base`)
attached to the search container's own AUI component instance, registered under
`searchContainerId`. This is the single authoritative object for everything selection-related —
confirmed by reading it directly, not inferred.

### Getting the live instance

```js
Liferay.componentReady(portletNamespace + 'myListSearchContainer').then(function (searchContainer) {
    // searchContainer.select is the plugin instance
});
```

`search_container.js` registers each instance under **two** caches simultaneously, keyed by the
search container's DOM id — `Liferay.SearchContainer.get(id)` (sync, returns `undefined` if not
yet registered) and `Liferay.component(id)` / `Liferay.componentReady(id)` (async, the Promise
resolves once registered). **Prefer `Liferay.componentReady`** — it also solves a real timing bug
([timing reference](bulk-actions-and-timing.md)), which a synchronous `Liferay.SearchContainer.get(id)` called too early would not.

### `searchContainer.select` API (all confirmed by reading the source)

| Member | Type | What it is |
|---|---|---|
| `.get('bulkSelection')` | `boolean` | True iff "select all" was used (via `toggleAllRows`). **This is the value to submit as your own "select everything matching" flag** — see [bulk server/client handling](bulk-actions-and-timing.md). |
| `.on('bulkSelectionChange', fn)` | event | Fires whenever `bulkSelection` changes — free via `A.Base`'s auto-generated `<attr>Change` events for anything in `ATTRS`. Only fires for the select-all/clear action, **not** individual row clicks. |
| `.on('rowToggled', fn)` | event | **The one to use for "did selection change at all."** `toggleRow()` (individual row click) *and* `toggleAllRows()` (select-all/clear) both funnel through `_notifyRowToggle()`, which fires this single unified event. Confirmed as the standard hook — used by Document Library's own `DocumentLibrary.js`, the toolbar's own `SelectionControls.js`, and a dozen+ other stock Liferay modules (`grep -rn "rowToggled" liferay-portal` to see them all). |
| `.getCurrentPageSelectedElements()` | AUI NodeList | Checked row elements on the current page only. Has `.size()`. Prefer this over `document.querySelectorAll('input[name="...rowIds"]:checked')` — same underlying data, but through the authoritative API instead of a parallel DOM query that can drift out of sync. |
| `.getAllSelectedElements()` | AUI NodeList | All selected elements the component knows about (used internally for session-storage restore across navigation). |
| `.toggleRow(config, row)` / `.toggleAllRows(selected, bulkSelection)` | methods | What the checkboxes' `onclick` handlers actually call — you don't need to call these yourself, just know they're what triggers `rowToggled`. |

---
