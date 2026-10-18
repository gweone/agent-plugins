---
name: codebase-memory-mcp-setup
description: Install or remove codebase-memory-mcp, register MCP clients, configure indexing, or build, refresh, share, and delete repository indexes. Covers global client/config/hooks/profile/skill changes, permission-safe setup, remote CLI operation, exact environment variables, and version-specific installer evidence; not graph exploration or architecture analysis.
---

# Codebase-memory setup and index lifecycle

Use for an explicitly requested installation, client configuration, or index lifecycle task.
Setup is not a prerequisite to answering an ordinary source-analysis question.
All examples are documentation; do not install, configure, or index automatically.

## Scope and consent

1. Confirm the host, repository root, desired client(s), and requested lifecycle operation.
2. Inspect existing binary/version, client settings, and indexed projects without changing them.
3. Explain that the documented installer can configure all detected clients globally:
   MCP entries, agent profiles, skills/instructions, and lifecycle hooks—not just a binary.
4. Read the current installer/configuration before writes; agree the intended changes first.
5. Preserve tool permission gates. After denial, stop; do not split, retry, delegate,
   or edit permission settings to bypass it. Offer a user-run manual handoff instead.

## Native client versus remote connector

- Native MCP clients need a coding-agent session restart after registration.
- A remote/sandbox shell connector has no local client session to restart on that host;
  use `codebase-memory-mcp cli <tool>` via its shell tool for every operation.
- Remote installer side effects are still global changes, not harmless binary-only setup.
- CLI mode neither starts nor connects to the coordination daemon and leaves no standing process.

## Index and verify

- Decide whether service boundaries require a shared root or separate service indexes.
- Index only the approved root; inspect `list_projects`, `index_status`, and `get_architecture`.
- Check expected languages/packages, not just a success response or a live `git.head_sha`.
- Saved uncommitted changes can evade default `auto_watch`; disclose drift before graph use.
- Ask before enabling auto-indexing, writing extension mappings, sharing artifacts, or deletion.
- Uninstall removes owned client configuration and may delete confirmed graphs; review scope first.

## Detailed references

- [Installation, clients, provenance, and cleanup](references/installation-and-clients.md)
  — v0.10.2 observations, exact installer, Windows guidance, global paths, and denial handling.
- [Indexing, configuration, and remote CLI](references/indexing-and-configuration.md)
  — first run, all environment variables, config commands, extension mapping, shared snapshots.

The recorded v0.10.2 behavior and historical provenance are evidence, not future-version guarantees.
