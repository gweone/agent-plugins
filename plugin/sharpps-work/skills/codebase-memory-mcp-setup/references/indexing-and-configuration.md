# Index lifecycle, remote CLI, and configuration

## Plan before changing state

Confirm the root and whether cross-service routes require one shared root or separately indexed
services. Identify existing projects first. Indexing stores persistent graph data; configuration
commands, custom extension files, shared artifacts, and deletion all require the appropriate
user-approved scope. Read existing files/settings before writing; do not silently enable automatic
indexing or background behavior.

## Remote shells and sandboxes

When this repo is reached over a remote shell/sandbox connector (e.g. SharpPS `shell_execute`)
rather than Claude Code running natively on the host, the MCP install/registration workflow for a native client
doesn't apply: there's no local Claude Code client session on that host to restart, and nothing
there will pick up an MCP entry written to `~/.claude.json`. In that situation, skip straight to
CLI mode and use it for every operation instead of MCP tools:

```bash
codebase-memory-mcp cli index_repository --repo-path <root_path>
codebase-memory-mcp cli list_projects
codebase-memory-mcp cli search_graph --project <project> --name-pattern '...' --label Function
codebase-memory-mcp cli trace_path --project <project> --function-name <name> --direction both
codebase-memory-mcp cli query_graph --project <project> --query '...'
codebase-memory-mcp cli index_status --project <project> --verbose true
```

If the binary is absent, request approval for setup first. The documented installer below
also changes any detected clients' global configuration/hooks/profiles/skills. It is not a
binary-only or harmless remote install; inspect its current behavior before approval:

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

After an approved remote install, do not wait for or reference an MCP tool restart here, and
don't call MCP tool names (`index_repository`, `search_graph`, etc.) directly; those only exist
inside an MCP client. Every read/query in this connection type goes through `cli`, using whatever
shell tool the connector provides (e.g. `shell_execute`).

## First run

In a native MCP client there is no dedicated first-run CLI command — after an approved
install and agent restart, request the approved indexing task in plain English:

> "Index this project."

The agent calls the `index_repository` MCP tool itself. For the Linux kernel (28M LOC, 75K files)
this completes in ~3 minutes; expect proportionally less for a single service/module.

Those first-run timings are an upstream example, not a performance promise.

## CLI equivalents (for scripting, no daemon involved)

```bash
codebase-memory-mcp cli index_repository --repo-path /path/to/repo
codebase-memory-mcp cli list_projects
codebase-memory-mcp cli search_graph --project my-project --name-pattern '.*Handler.*' --label Function
codebase-memory-mcp cli trace_path --project my-project --function-name Search --direction both
codebase-memory-mcp cli query_graph --project my-project --query 'MATCH (f:Function) RETURN f.name LIMIT 5'
```

`cli` mode neither starts nor connects to the coordination daemon and leaves no standing process
behind — use it when you want a one-shot answer without the MCP/agent round-trip.

## Configuration

Env vars (all optional, sane auto-detected defaults):

| Var | Default | Purpose |
|---|---|---|
| `CBM_CACHE_DIR` | `~/.cache/codebase-memory-mcp` | Database storage location |
| `CBM_ALLOWED_ROOT` | unset | Confine indexing to paths under this directory |
| `CBM_WORKERS` | auto | Parallel indexing worker count (1-256) |
| `CBM_MEM_BUDGET_MB` | auto | In-memory graph budget cap |
| `CBM_LOG_LEVEL` | `info` | debug/info/warn/error/none |

```bash
codebase-memory-mcp config list
codebase-memory-mcp config set auto_index true        # index automatically on session start
codebase-memory-mcp config set auto_index_limit 50000  # cap for auto-indexing
codebase-memory-mcp config set auto_watch false         # disable background re-index watcher
```

Custom extension mapping per-repo via `.codebase-memory.json`:
```json
{"extra_extensions": {".blade.php": "php", ".mjs": "javascript"}}
```

## Language coverage

158 languages via vendored tree-sitter grammars, in quality tiers — check before relying on
results for an unusual language:
- **Excellent (≥90%)**: Lua, Kotlin, C++, Perl, Objective-C, Groovy, C, Bash, Zig, Swift, CSS,
  YAML, TOML, HTML, SCSS, HCL, Dockerfile
- **Good (75-89%)**: Python, TypeScript, TSX, Go, Rust, Java, R, Dart, JavaScript, Erlang, Elixir,
  Scala, Ruby, PHP, C#, SQL
- **Functional (<75%)**: OCaml, Haskell

Full Hybrid-LSP semantic resolution (not just AST) currently covers: Python, TypeScript/
JavaScript/JSX/TSX, PHP, C#, Go, C, C++, Java, Kotlin, Rust, Perl.

## Team-shared graph artifact

A repo can commit `.codebase-memory/graph.db.zst` (zstd-compressed SQLite snapshot) so teammates
skip full reindexing — they decompress and run an incremental index instead. Worth doing for a
large/slow-to-index repo shared across a team, not for a solo/throwaway index.

Do not commit or distribute a graph artifact automatically; confirm ownership, source-data
sensitivity, and the intended recipients first. `delete_project` removes an indexed project;
confirm the exact project and deletion before using it.

## Verify the result

Inspect `list_projects`, `index_status` (including verbose output), and `get_architecture`
after indexing. Cross-check expected languages/packages against the checkout. A live
`git.head_sha` is not an indexed revision marker; dirty worktree edits can evade `auto_watch`.
Before later analysis, recheck working-tree drift and disclose incomplete coverage.
