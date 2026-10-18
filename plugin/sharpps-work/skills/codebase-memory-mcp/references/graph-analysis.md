# Graph analysis and evidence

[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) is a self-contained native
binary (no language runtime dependency) that builds a persistent knowledge graph of a codebase —
tree-sitter AST parsing across 158 languages, plus a lightweight semantic type-resolution layer
(a mini language-server inspired by tsserver/pyright/gopls/rust-analyzer) for things AST alone
can't resolve: dotted attribute access, generic types, inheritance chains. It's exposed to Claude
Code as an **MCP server** (15 tools), not a slash command — so once installed and configured, you
ask questions in plain English and the agent calls the tools directly, no CLI syntax needed in the
prompt itself.

**Why this over a pure-AST tool**: it explicitly does HTTP route ↔ call-site matching (with
confidence scoring) plus gRPC/GraphQL/tRPC/Socket.IO detection across languages — so a frontend
`fetch('/api/orders')` call *can* link to the backend controller that serves it, something a
plain per-language call-graph tool can't do. Worth reaching for specifically when tracing a
request across a polyglot/microservice boundary, which is exactly where AST-only tools stop short.

**Cross-platform**: ships as a self-contained binary for macOS (arm64/amd64), Linux (arm64/amd64),
and Windows (amd64) — no Node/Python runtime needed to run it (only a C/C++ compiler + zlib
headers + git at build/verify time per the install script's requirements check).

## MCP tools (what the agent actually calls)

No slash-command syntax to remember — these fire from natural-language questions once installed:

| Tool | Use |
|---|---|
| `index_repository` / `index_status` / `list_projects` / `delete_project` | Build and manage the graph |
| `search_graph` | Structured search by label/name-pattern/degree, with pagination |
| `search_code` | Grep-like text search scoped to indexed files |
| `trace_path` | BFS caller/callee traversal, depth 1-5 |
| `detect_changes` | Map a git diff to affected symbols with risk classification |
| `query_graph` | Read-only Cypher-like query for custom traversals |
| `get_architecture` | Overview: languages, packages, routes, clusters |
| `get_code_snippet` | Fetch source for a function by qualified name |
| `get_graph_schema` | Node/edge counts and relationship patterns |
| `manage_adr` | CRUD on Architecture Decision Records |
| `ingest_traces` | Feed runtime traces in to validate HTTP edges |

`index_repository` and `delete_project` mutate index state; `manage_adr` can write
ADRs and `ingest_traces` changes graph evidence. This inventory is not permission
to call them during exploration. Obtain approval for the specific lifecycle/write task.

## CLI equivalents (for scripting, no daemon involved)

```bash
codebase-memory-mcp cli list_projects
codebase-memory-mcp cli search_graph --project my-project --name-pattern '.*Handler.*' --label Function
codebase-memory-mcp cli trace_path --project my-project --function-name Search --direction both
codebase-memory-mcp cli query_graph --project my-project --query 'MATCH (f:Function) RETURN f.name LIMIT 5'
```

`cli` mode neither starts nor connects to the coordination daemon and leaves no standing process
behind — use it when you want a one-shot answer without the MCP/agent round-trip.

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

## Verification

Don't trust a graph answer at face value for anything consequential:
- Cross-check `get_architecture` output's language/package list against what you already know
  about the repo — a near-empty result usually means indexing silently skipped most files.
- For cross-service HTTP route claims specifically, check the **confidence score** `trace_path`/
  `search_graph` returns — this is inferred matching, not guaranteed-correct static linkage like
  a same-language function call.
- `detect_changes` risk classifications are a starting point for review, not a substitute for
  actually reading the diff on anything flagged high-risk.

Coverage is not completeness: validate relevant source and use filesystem read/search
when the graph misses files or cannot support a negative claim. Language tier percentages
are upstream evidence, not guarantees for every framework or repository.
