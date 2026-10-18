---
name: liferay-management-toolbar-search-container
description: >
  Fix clay:management-toolbar with liferay-ui:search-container/RowChecker bulk selection, select-all pagination bugs, missing submitted checkboxes, rowToggled timing and propsTransformer onActionButtonClick. Read bulkSelection via componentReady and recompute matching rows server-side.
---

# Liferay management toolbar and search container

The toolbar's select-all checkbox is client state, not a submitted form field.
The references retain source tracing and live `modules/search` debugging from
another consuming workspace; resolve current paths and release before applying.

## Workflow

1. Render `<clay:management-toolbar>` **outside/before** `<aui:form>`.
   With search enabled the toolbar owns a search form; nesting forms breaks
   checkbox association and submission.
2. Pair toolbar and search container using the same resolved/namespaced
   `searchContainerId`; they need no parent/child DOM relationship.
3. Await `Liferay.componentReady(searchContainerId)` and read
   `sc.select.get('bulkSelection')`, not header checkbox attributes or `.checked`.
4. Subscribe to `rowToggled` for both single-row and select-all/clear changes.
   `bulkSelectionChange` alone misses individual row clicks.
5. Immediately before submit, set your hidden `selectAll` flag and include
   the current filter criteria. Normal row checkboxes submit explicit row IDs.
6. On the server, recompute **all matching rows** with the same filter logic
   when `selectAll` is true. Validate scope, filters and per-item permissions.
7. Wire toolbar dropdown actions with `propsTransformer` and
   `onActionButtonClick(event, {item})`, matching `item.data.action`.
8. Resolve plain sibling elements inside `componentReady`; for uncertain React
   mounts use a supported prop, or stable delegated listeners as a fallback.

## Critical constraints

- The React header checkbox has no submitted name/value. Select-all can label
  76 selected while only 20 current-page `rowIds` are physically present.
- Do not inflate SearchContainer delta to simulate bulk selection, submit an
  unbounded client-side ID array, or revive legacy `RowChecker.getAllRowsCheckbox()`.
- `getCurrentPageSelectedElements()` is current-page-only; the AUI component is
  authoritative, not a parallel checkbox query.
- A later JSP `<aui:script>` can execute before sibling HTML exists; observed
  root cause was not fully pinned down. Do not assume source order is readiness.
- New npm-scripts files were observed missing from incremental output despite
  success. Inspect artifacts and use the consuming project's approved clean-build
  workflow; adding an export alone does not prove it shipped.

## Focused references

- [JSP structure, React/AUI architecture and selection API](references/structure-and-selection.md)
- [Timing, full server/client examples, propsTransformer and source evidence](references/bulk-actions-and-timing.md)

`modules/search` paths and helper methods in examples belong to the earlier
consuming application, not this plugin repository or generic Liferay APIs.
