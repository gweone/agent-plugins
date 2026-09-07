---
name: liferay-management-toolbar-search-container
description: Use whenever building, fixing, or reviewing a Liferay admin JSP that combines clay:management-toolbar with selectable=true with liferay-ui:search-container + `com.liferay.portal.kernel.dao.search.RowChecker` — bulk-select checkboxes, a "select all" header checkbox, and a bulk action (delete/add/export) on checked rows. Trigger for "select all doesn't select everything", "select all only adds/deletes N items" (N usually the default page size), "bulk delete not working", "checkbox not submitting", "management toolbar checkbox has no name attribute", "RowChecker", "bulkSelection", "searchContainer.select", "rowToggled event", "propsTransformer for management toolbar", "onActionButtonClick", or any JSP combining these two taglibs with a bulk-action button/dropdown item. Confirmed via live debugging in `modules/search` admin config screens and by reading the real `liferay-portal` source.
---

# Management Toolbar + Search Container: Selection & Bulk Actions

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
  registered under that id (see Section 3), not by any parent/child DOM relationship.

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
3. Its click handler ultimately calls `toggleAllRows()` on the shared AUI component (Section 3),
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
(Section 4), which a synchronous `Liferay.SearchContainer.get(id)` called too early would not.

### `searchContainer.select` API (all confirmed by reading the source)

| Member | Type | What it is |
|---|---|---|
| `.get('bulkSelection')` | `boolean` | True iff "select all" was used (via `toggleAllRows`). **This is the value to submit as your own "select everything matching" flag** — see Section 5. |
| `.on('bulkSelectionChange', fn)` | event | Fires whenever `bulkSelection` changes — free via `A.Base`'s auto-generated `<attr>Change` events for anything in `ATTRS`. Only fires for the select-all/clear action, **not** individual row clicks. |
| `.on('rowToggled', fn)` | event | **The one to use for "did selection change at all."** `toggleRow()` (individual row click) *and* `toggleAllRows()` (select-all/clear) both funnel through `_notifyRowToggle()`, which fires this single unified event. Confirmed as the standard hook — used by Document Library's own `DocumentLibrary.js`, the toolbar's own `SelectionControls.js`, and a dozen+ other stock Liferay modules (`grep -rn "rowToggled" liferay-portal` to see them all). |
| `.getCurrentPageSelectedElements()` | AUI NodeList | Checked row elements on the current page only. Has `.size()`. Prefer this over `document.querySelectorAll('input[name="...rowIds"]:checked')` — same underlying data, but through the authoritative API instead of a parallel DOM query that can drift out of sync. |
| `.getAllSelectedElements()` | AUI NodeList | All selected elements the component knows about (used internally for session-storage restore across navigation). |
| `.toggleRow(config, row)` / `.toggleAllRows(selected, bulkSelection)` | methods | What the checkboxes' `onclick` handlers actually call — you don't need to call these yourself, just know they're what triggers `rowToggled`. |

---

## 4. Timing: `<aui:script>` can run before the surrounding HTML exists

Confirmed via live console debugging: a `<aui:script>` block placed after the search container
in a JSP can execute **before** the form/button/hidden-fields it references exist in the DOM —
`document.getElementById(...)` for all of them returned `null` at that point, even though they
were all part of the same server-rendered HTML block. (Root cause not fully pinned down — could
be `<aui:script>` batching/hoisting, could be how this popup config screen's content gets
inserted — but the fix doesn't require knowing exactly why.)

**Never do a one-shot `document.getElementById(...)` at the top level of the script and assume it
succeeded.** Two valid patterns, depending on what you're looking up:

### Pattern A — plain server-rendered elements: defer via `Liferay.componentReady`

If the element (a button, a hidden input, the form itself) is part of the **same
server-rendered HTML block** as the search container, `Liferay.componentReady(searchContainerId)`
resolving is a reliable enough signal that it also exists — grab it *inside* the `.then()`:

```js
Liferay.componentReady(searchContainerId).then(function (sc) {
    var button = document.getElementById(ns + 'mySubmitButton'); // safe now
    if (!button) return;

    button.addEventListener('click', function () { ... });
});
```

### Pattern B — elements with uncertain/dynamic mount timing: delegate

For anything whose mount timing you *can't* reason about this way — most importantly, **React-
rendered elements inside the toolbar itself** (the action dropdown's menu items in particular;
`ClayDropDownWithItems` may or may not keep them in the DOM between opens, and there's no
equivalent "ready" signal for them the way there is for the search container) — delegate on a
stable, always-present ancestor instead of trying to grab the element directly:

```js
document.body.addEventListener('click', function (e) {
    if (!e.target.closest('[data-action="myBulkAction"]')) return;
    // ...
});
```

Delegation is correct here regardless of whether the target was there all along, got created
late, or gets torn down and recreated on every open/close — `closest()` resolves against
whatever's live in the DOM *at click time*. A one-shot direct-attach is only safe under Pattern A;
don't apply it to Pattern B elements just because it worked for a plain button.

**Better than either, when available: use `propsTransformer` (Section 6)** — it sidesteps the
whole DOM-timing question for anything the toolbar's React tree owns.

---

## 5. Making "select all" actually mean "every matching item"

Don't try to submit a JS-embedded array of every matching row's key — unbounded size, spoofable,
and pointless complexity. **Mirror Liferay's own pattern** (confirmed by reading Document
Library's `BulkSelectionFactoryUtil`/`FileEntryBulkSelectionFactory`, which does exactly this):
submit a boolean flag plus the same filter criteria the page was rendered with, and have the
**server** recompute the actual matching set.

### JSP: a hidden flag, populated right before submit

```jsp
<input name="<portlet:namespace />selectAll" type="hidden" value="false" />
<%-- also mirror whatever filter criteria your list uses, e.g.: --%>
<input name="<portlet:namespace />keywords" type="hidden" value="<%= HtmlUtil.escapeAttribute(keywords) %>" />
```

```js
Liferay.componentReady(searchContainerId).then(function (sc) {
    // ... elsewhere, right before form.submit():
    selectAllHidden.value = (sc.select && sc.select.get('bulkSelection')) ? 'true' : 'false';
});
```

### Action class: recompute, don't trust the submitted `rowIds`

```java
boolean selectAll = "true".equals(_val(ap, "selectAll"));
String[] rowIds = ap.getValues("rowIds");
if (!selectAll && (rowIds == null || rowIds.length == 0)) return;

if (selectAll) {
    // Recompute using the SAME filter logic the JSP used to render the
    // page — duplicated here because a JSP-declared method isn't
    // callable from this class. Keep the two in sync with a comment
    // pointing at each other.
    rowIds = _matchingRowIds(fullCandidateList, _val(ap, "keywords"));
}

for (String rowId : rowIds) {
    // existing per-row handling, unchanged
}
```

This is strictly more correct than trusting the client: it works for any list size (no pagination
ceiling), it's not spoofable (the server decides what "all" means, not the client), and pagination
keeps working normally for browsing since nothing about page size changes.

**Do not try to fix this by inflating the `SearchContainer`'s delta/page size so everything
renders on one page.** That was an earlier, wrong attempt in this project — it "solves" select-all
by defeating pagination entirely, which breaks down again the moment the list is large enough
that even the inflated delta isn't enough, and gives up real browsing UX for no good reason.

---

## 6. The idiomatic version: `propsTransformer`

For anything the toolbar's action dropdown owns (a bulk action with no `href`, wired via
`DropdownItem#putData("action", "myAction")`), the click only ever reaches you through a real
React prop — `onActionButtonClick(event, {item})` — not any DOM event you can reliably delegate
around forever. This is confirmed as the exact stock pattern via
`asset-categories-admin-web`'s `AssetCategoriesManagementToolbarPropsTransformer.js`:

```js
// AssetCategoriesManagementToolbarPropsTransformer.js (real, stock Liferay)
export default function propsTransformer({portletNamespace, ...otherProps}) {
    return {
        ...otherProps,
        onActionButtonClick(event, {item}) {
            const action = item?.data?.action;
            if (action === 'deleteSelectedCategories') {
                deleteSelectedCategories();
            }
        },
    };
}
```

### Wiring it up

1. Add `propsTransformer="{YourFunctionName} from <npm-package-name>"` to the
   `<clay:management-toolbar>` tag (`<npm-package-name>` = your module's `package.json` `"name"`).
2. Export the function from your module's `js/index.ts` barrel, same convention as any other
   hydrated component (`export {default as YourFunctionName} from './YourFunctionName';`).
3. Inside, match on `item.data.action` and do whatever the click should do — read
   `bulkSelection` via `Liferay.componentReady`, sync a hidden field, `form.submit()`.

This eliminates the DOM-timing question from Section 4 (Pattern B) entirely for anything routed
through it — replace `document.body.addEventListener('click', ...)` delegation with this once
it's set up; keep delegation only where no propsTransformer is wired up yet.

Other props `ManagementToolbar.js` forwards that may be useful depending on what you're
intercepting: `onFilterDropdownItemClick`, `onCreateButtonClick`, `onCheckboxChange` (fires on the
select-all checkbox's own change, before `rowToggled`'s broader net), `onClearSelectionButtonClick`,
`onSelectAllButtonClick`. Grep `ManagementToolbar.js`'s prop list before assuming one exists —
don't guess a name.

### Build gotcha: clear the build dir for brand-new files

`liferay-npm-scripts build`'s incremental cache can **silently omit a file that didn't exist on
the previous build** — confirmed empirically: a first build after adding a new `.ts` file
produced a bundle with zero references to it (verified via `grep` on the compiled output), while
every pre-existing export was still present and correctly updated. A `rm -rf build && npm run
build` (or your project's equivalent clean-build step) fixed it immediately. **Whenever adding a
new propsTransformer/component file for the first time, do a clean build before assuming the
bundle is correct** — don't just trust "the build succeeded with no errors."

---

## 7. Quick checklist

- [ ] Toolbar rendered **before/outside** the `<aui:form>` it's paired with (Section 1).
- [ ] Never read "was select-all used" from a checkbox's `.checked`/`name` — there isn't one to
      read. Use `Liferay.componentReady(searchContainerId).then(sc => sc.select.get('bulkSelection'))`.
- [ ] "Select all" resolved server-side by recomputing the matching set from filter criteria +
      a `selectAll` flag — never by inflating the page size, never by trusting a client-submitted
      list of every matching id.
- [ ] Individual selection-changed reactions (enabling a button, updating a count) subscribe to
      `sc.on('rowToggled', fn)` — covers both single-row and select-all/clear in one hook.
- [ ] Any element looked up in a `<aui:script>` is either grabbed lazily inside
      `Liferay.componentReady(...).then()` (plain server-rendered siblings) or found via
      delegation on a stable ancestor (anything React-owned with uncertain mount timing) — never
      a bare top-level `document.getElementById(...)` assumed to succeed immediately.
- [ ] Custom `actionDropdownItems` (no `href`) wired via a `propsTransformer`'s
      `onActionButtonClick`, matching `item.data.action`, not raw `document.body` click
      delegation — unless no propsTransformer is set up yet for that toolbar.
- [ ] After adding a **new** propsTransformer/JS file, clean-build (`rm -rf build`) before
      trusting the bundle.

## Reference implementation in this repo

`modules/search/src/main/resources/META-INF/resources/results/display/configuration/` —
`field_form.jsp` (plain-button case, Pattern A + `rowToggled` + `getCurrentPageSelectedElements`),
`view_fields.jsp`/`view_filters.jsp`/`view_sortings.jsp`/`views_list.jsp` (dropdown-action case,
now wired via `propsTransformer`) — and
`modules/search/src/main/resources/META-INF/resources/js/AdminBulkActionsPropsTransformer.ts` (the
shared propsTransformer, routing multiple actions per toolbar — e.g. `bulkDeleteFields` and
`bulkSyncFields` both share `view_fields.jsp`'s toolbar/form), plus the matching server-side
`selectAll` handling in `DisplaySearchResultsPortletConfigurationAction.java`'s
`_handleSaveFieldsFromSelection`, `_handleBulkSyncFields`, `_handleBulkDeleteItems`, and
`_handleBulkDeleteViews`.
