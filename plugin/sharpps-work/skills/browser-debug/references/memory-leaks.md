# Memory leaks

Summarized from the upstream `memory-leak-debugging` skill. Use for high memory use, OOM
errors, or when asked to capture, compare, or inspect heap snapshots.

## Prerequisites and rules

- Heap analysis tools (`get_heapsnapshot_*`, `compare_heapsnapshots`, and so on) exist
  only when the server runs with `--memoryDebugging`. If they are missing, read the MCP
  config to check the flag, and ask the user to add it and restart the client.
- Never read a raw `.heapsnapshot` file; it is enormous. Use the MCP tools to summarize,
  compare, and drill in.
- Decide whether the leak is client-side (browser) or server-side (Node.js).
- Call `close_heapsnapshot` on every loaded snapshot afterwards to free server memory.

## Capture

1. Drive the page to the starting state, then `take_heapsnapshot` (baseline; saves a
   `.heapsnapshot` file under the path you give it).
2. Repeat the suspect interaction about 10 times (`click`, `navigate_page`, `fill`) to
   amplify the leak, then `take_heapsnapshot` (target).
3. Revert the page to its original state and `take_heapsnapshot` (final) to see whether
   memory is released.

## Compare, then drill down

1. `get_heapsnapshot_summary` on each file to confirm it loads and compare totals.
2. `compare_heapsnapshots` baseline vs. target without `classIndex` for the summary diff;
   request a class diff (`classIndex`) only for suspicious growth.
3. For a growing class: `get_heapsnapshot_class_nodes` lists instances, then
   `get_heapsnapshot_retainers`, `get_heapsnapshot_retaining_paths`,
   `get_heapsnapshot_dominators`, `get_heapsnapshot_edges` explain why they stay
   reachable, and `get_heapsnapshot_object_details` (by `nodeId`) gives size, type,
   distance, and DOM detachedness. Use `get_heapsnapshot_duplicate_strings` when strings
   dominate.
4. Shortcut filters (`filterName` on `get_heapsnapshot_details` or
   `get_heapsnapshot_class_nodes`): `objectsRetainedByDetachedDomNodes`,
   `objectsRetainedByEventHandlers`, `objectsRetainedByContexts` (closures),
   `objectsRetainedByConsole`.

Only change code once the retaining path points at application code.

## Common causes and fixes

| Cause | Fix |
|---|---|
| Event listeners on `window`/`document`/long-lived objects never removed | `removeEventListener` on unmount or when no longer needed |
| Detached DOM nodes still referenced by a variable | Tell the user first. Detached nodes are sometimes an intentional cache, so **ask before nulling references or editing code**; if confirmed, null the reference on removal or narrow its scope |
| Accidental globals (undeclared variables, `window.x`) | Strict mode; declare variables; avoid global state |
| Closures holding large outer-scope objects | Null the object when done, or stop capturing it |
| Unbounded caches, arrays, Maps | Size limits, LRU, or `WeakMap`/`WeakSet` for per-object data |
