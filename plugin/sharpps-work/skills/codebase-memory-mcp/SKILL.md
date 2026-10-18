---
name: codebase-memory-mcp
description: Explore an already available codebase-memory-mcp knowledge graph to map code architecture, trace callers/callees and HTTP routes across services, or assess change impact. Covers graph queries, CLI analysis on remote shells, freshness checks, language coverage, and confidence limits; not installation, client configuration, or index lifecycle management.
---

# Codebase-memory graph exploration

Use an existing graph for architecture, call-graph, cross-service, and change-impact analysis.
Do not install or reconfigure clients merely to answer an analysis question.
If the binary, tools, or index are missing, report that and ask whether setup is wanted.

## Scope and planning

1. Confirm the repository root, project name, and question.
2. For polyglot systems, establish whether the question crosses service boundaries.
3. Discover existing projects with `list_projects` and inspect `index_status`.
4. Check freshness and coverage before treating graph output as evidence.
5. Query narrowly, inspect source for consequential claims, and report limitations.

## Choose the available interface

- In a configured MCP client, call the MCP tools directly; no slash command is needed.
- Over a sandbox/remote connector, use `codebase-memory-mcp cli <tool>` through
  the connector's shell tool (for example `shell_execute`), not bare MCP tool names.
- CLI mode neither starts nor connects to the coordination daemon and leaves no
  standing process. Client registration on the remote host does not expose tools here.
- Analysis does not authorize indexing, ADR writes, runtime-trace ingestion, or deletion.

## Evidence gates

- Unless indexed in this conversation with no subsequent edits, check the indexed
  root for uncommitted changes. Default `auto_watch: true` missed saved edits in testing.
- `index_status --verbose true` reports a live `git.head_sha`, not the indexed revision.
- A dirty tree means possible drift: disclose it and offer an explicitly approved reindex.
- Validate language/package coverage; near-empty graphs can reflect skipped files.
- HTTP route matching is inferred: inspect confidence, not just a returned edge.
- Risk classifications guide review; they do not replace reading the actual diff.

## Detailed references

- [Graph model, tools, language tiers, and verification](references/graph-analysis.md)
  — native binary, semantic resolution, 15-tool inventory, CLI query examples, and caveats.
- [Freshness checks and working-tree drift](references/freshness.md)
  — tested watcher behavior, exact status command, and reindex decision.

All command examples are documentation, not instructions to install or mutate state automatically.
