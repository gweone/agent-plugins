# Bulk action wiring, timing and server recomputation

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

**Better than either, when available: use [the propsTransformer pattern](bulk-actions-and-timing.md)** — it sidesteps the
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

This eliminates the DOM-timing question for [uncertain React mount timing (Pattern B)](bulk-actions-and-timing.md) entirely for anything routed
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

- [ ] Toolbar rendered **before/outside** the `<aui:form>` it's paired with ([toolbar structure](structure-and-selection.md)).
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

## Reference implementation in the original consuming workspace

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

Security qualification: server recomputation avoids trusting a client-provided full
ID list, but is not authorization by itself. Validate submitted filters, tenant/site
scope and per-item permissions for both bulk and explicit-row paths. `_val`, `ap` and
`_matchingRowIds` are consuming-module helpers in the illustration, not platform APIs.
