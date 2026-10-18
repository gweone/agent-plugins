# Freshness before graph-backed answers

**Confirmed by direct testing**: `auto_watch: true` (the default) did **not** trigger a reindex
for a real, saved content edit to a file inside an already-indexed project — waited 20+ seconds,
checked the daemon log, nothing fired. Whatever background sync exists appears to be git-commit
based (per the docs' own "background git-based change detection" wording), not filesystem-watch
based — so a plain uncommitted edit can silently leave the graph stale with no automatic recovery.

**Also confirmed**: `index_status --verbose true`'s `git.head_sha` field is a **live** read of the
current `git rev-parse HEAD` at query time, not a value stored from when the project was indexed —
it doesn't change to reflect drift and can't be used to detect staleness on its own.

**What actually works**: before trusting a graph-backed answer (query_graph, trace_path,
search_graph, etc.) on a project you didn't just index in this same conversation, check for
uncommitted changes in the indexed root first:

```bash
git -C <root_path> status --porcelain -- <path-relative-to-repo-root>
```

If that returns anything, the graph may not reflect the current working tree. Tell the user and
offer to re-index (`codebase-memory-mcp cli index_repository --repo-path <root_path>`, or just ask
the agent to re-index) before answering, rather than silently serving a possibly-stale result. Skip
this check only when the index was just built earlier in the same conversation and nothing has
changed since.

Reindexing writes persistent graph state. Offer it, explain scope, and obtain approval
before running it; otherwise use current source and label graph evidence provisional.
