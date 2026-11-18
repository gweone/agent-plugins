---
name: codebase-memory-mcp
description: Work with a codebase-memory-mcp knowledge graph. Explore an existing graph to map code architecture, trace callers/callees and HTTP routes across services, or assess change impact (graph queries, CLI mode on remote shells, freshness checks, language coverage, confidence limits). Also covers, only when explicitly requested, installing or removing the tool, registering MCP clients, configuring indexing, and building, refreshing, sharing, or deleting repository indexes (global client/config/hook/profile/skill changes, permission-safe setup, environment variables, version-specific installer evidence). Analysis alone never authorizes setup or index writes.
---

# Codebase-memory knowledge graph

[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) builds a persistent
graph of a codebase and exposes it as MCP tools or one-shot `cli` calls. This skill has two
modes with one hard boundary: **exploring** an existing graph is read-only; **setup and index
lifecycle** changes state and needs an explicit request.

## Pick the mode

| Task | Mode | Start with |
|---|---|---|
| Architecture, call graph, cross-service routes, change impact on an existing index | Explore | [graph analysis](references/graph-analysis.md), then [freshness](references/freshness.md) |
| Install or uninstall, register an MCP client, change config, index / reindex / share / delete a project | Setup | [installation and clients](references/installation-and-clients.md) or [indexing and configuration](references/indexing-and-configuration.md) |

Setup is not a prerequisite to answering an ordinary source-analysis question. If the binary,
tools, or index are missing during exploration, report that and ask whether setup is wanted;
do not switch modes or install/reconfigure clients on your own.

## Choose the available interface

- In a configured native MCP client, call the MCP tools directly; no slash command is needed.
  A client reads its MCP config at startup, so a coding-agent session restart is required after
  registration.
- Over a sandbox/remote connector, use `codebase-memory-mcp cli <tool>` through the connector's
  shell tool (for example `shell_execute`), not bare MCP tool names. Client registration on the
  remote host does not expose tools here, and there is no local client session to restart.
- CLI mode neither starts nor connects to the coordination daemon and leaves no standing process.
- Remote installer side effects are still global changes, not harmless binary-only setup.

## Explore workflow: Spec → Plan → Query → Report

1. **Spec** — confirm the repository root, project name, and question. For polyglot systems,
   establish whether the question crosses service boundaries.
2. **Plan** — discover existing projects with `list_projects`, inspect `index_status`, and check
   freshness and coverage before treating graph output as evidence.
3. **Query** — query narrowly; read the source for consequential claims.
4. **Report** — state findings with their limits: coverage gaps, working-tree drift, inferred
   (confidence-scored) edges.

Evidence gates:

- Unless indexed in this conversation with no subsequent edits, check the indexed root for
  uncommitted changes. Default `auto_watch: true` missed saved edits in testing.
- `index_status --verbose true` reports a live `git.head_sha`, not the indexed revision.
- A dirty tree means possible drift: disclose it and offer an explicitly approved reindex.
- Validate language/package coverage; near-empty graphs can reflect skipped files.
- HTTP route matching is inferred: inspect confidence, not just a returned edge.
- Risk classifications guide review; they do not replace reading the actual diff.
- Analysis does not authorize indexing, ADR writes, runtime-trace ingestion, or deletion.

## Setup workflow: Spec → Consent → Execute → Verify

Use only for an explicitly requested installation, client configuration, or index lifecycle task.

1. **Spec** — confirm the host, repository root, desired client(s), and requested lifecycle
   operation. Inspect the existing binary/version, client settings, and indexed projects
   without changing them.
2. **Consent** — explain that the documented installer can configure all detected clients
   globally (MCP entries, agent profiles, skills/instructions, lifecycle hooks), not just a
   binary. Read the current installer/configuration before writes and agree the intended changes.
3. **Execute** — run only the approved steps. Decide whether service boundaries require a
   shared root or separate service indexes, and index only the approved root. Ask before
   enabling auto-indexing, writing extension mappings, sharing artifacts, or deleting.
4. **Verify** — inspect `list_projects`, `index_status`, and `get_architecture`. Check expected
   languages/packages, not just a success response or a live `git.head_sha`. Saved uncommitted
   changes can evade default `auto_watch`; disclose drift before graph use.

Uninstall removes owned client configuration and may delete confirmed graphs; review the scope
first.

## Core rules

- All command examples in this skill are documentation, not instructions to install,
  configure, or index automatically.
- Preserve tool permission gates. After a denial, stop; do not split, retry, delegate, or edit
  permission settings to bypass it. Offer a user-run manual handoff instead.
- Coverage is not completeness: use filesystem read/search when the graph misses files or
  cannot support a negative claim.
- The recorded v0.10.2 behavior and historical provenance are evidence, not future-version
  guarantees.

## Detailed guidance

- [Graph model, tools, language tiers, and verification](references/graph-analysis.md): native
  binary, semantic resolution, 15-tool inventory, CLI query examples, and caveats.
- [Freshness checks and working-tree drift](references/freshness.md): tested watcher behavior,
  exact status command, and reindex decision.
- [Installation, clients, provenance, and cleanup](references/installation-and-clients.md):
  v0.10.2 observations, exact installer, Windows guidance, global paths, and denial handling.
- [Indexing, configuration, and remote CLI](references/indexing-and-configuration.md): first
  run, all environment variables, config commands, extension mapping, shared snapshots.
