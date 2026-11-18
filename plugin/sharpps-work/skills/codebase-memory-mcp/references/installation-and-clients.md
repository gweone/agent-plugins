# Installation, client registration, and cleanup

## Approval and permission boundaries

Installation is not an analysis prerequisite. First confirm the intended host, installation
location, detected-client scope, and whether global config/hooks/profiles/skills may change.
Inspect existing configuration before writes; describe the intended changes and get explicit
approval. Do not change settings to grant yourself permission or bypass a blocked action.

The following commands are examples for an approved setup task, not automatic steps.

**One command does both the binary fetch and the agent registration** (confirmed in practice on
v0.10.2 — the README's own wording implies these are two separable steps, `install.sh` then
`codebase-memory-mcp install`, but running `install.sh` alone produced a fully configured install:
binary present, MCP entry in `~/.claude.json`, agent profiles in `~/.claude/agents/`, skill file in
`~/.claude/skills/codebase-memory/`, and `PreToolUse`/`PostToolUse`/`SessionStart` hooks in the
**global** `~/.claude/settings.json`, not project-scoped):

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```
(Windows: `Invoke-WebRequest ... install.ps1` then `.\install.ps1` — see the repo's README for
the exact PowerShell sequence.)

Under the hood this: downloads the release binary to `~/.local/bin/codebase-memory-mcp`, verifies
its SHA-256 against the published `checksums.txt`, does a `--version` smoke-test, then auto-detects
**all** supported clients present (43 surfaces — Claude Code, Cursor, VS Code, Zed, etc., not just
Claude) and configures each: MCP server registration, agent profile files (Scout/Verify/Auditor —
progressively broader graph access), skill/instruction files, and lifecycle hooks that inject
graph context into `Grep`/`Glob` calls. That's a real, global change to tool-call behavior across
every detected client on the machine — not project-scoped, not reversible by just deleting a repo
folder — so it's worth being upfront that this one command does more than "download a binary"
before running it, even though it's phrased as a single low-ceremony install line.

(Historical legitimacy check recorded when the original skill was written: 38.7k-star repo, MIT license, SLSA-3 build
provenance, Sigstore-signed releases, checksum enforcement in the script itself — historical provenance evidence, not a current safety guarantee. Inspect the downloaded
script and current release provenance before execution; do not treat those historical
counts or signatures as authorization. There's also a `codebase-memory-mcp install [--skip-config] [--dir=<path>]` subcommand
documented separately for re-running just the agent-config step — useful if the binary's already
present and only the client registration needs to be redone or targeted at a specific `--dir`.)

**A restart of the coding-agent session is required** before the new MCP tools are actually usable
— standard MCP behavior, clients read their MCP config at startup, so the session that ran the
install won't see the new tools itself. Say this explicitly rather than assuming the tools are
live immediately.

Matching cleanup: `codebase-memory-mcp uninstall` removes owned config entries, skills, hooks, and
instructions (lists indexed graphs for confirmation before deleting any of them) — explain the removal scope and get approval first. If denied, stop and offer a
manual handoff; do not bypass the permission boundary.

## Recorded auto-mode denial

**Confirmed in the recorded auto-mode session**: `curl | bash` (or downloading the
script first and running it as a separate step — tried both) was denied by Claude Code's
auto-mode permission classifier as "fetching and executing an external binary." Both
attempts and a `settings.json` permission edit were blocked. This is evidence about
that session, not a promise about all current clients or permission modes. Treat any
such denial as a permission boundary, not a fault to work around.

After a denial, stop: do not retry, split the command, delegate execution, or alter permissions
to evade it. Offer the exact documented command for the user to review and run in their own
terminal if they choose, then continue only after they confirm completion. A normally approved
interactive install may proceed, but do not attempt it merely to discover whether it is blocked.

## Platform and source

**Cross-platform**: ships as a self-contained binary for macOS (arm64/amd64), Linux (arm64/amd64),
and Windows (amd64) — no Node/Python runtime needed to run it (only a C/C++ compiler + zlib
headers + git at build/verify time per the install script's requirements check).

Source: [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp).
The installer URL tracks `main`; the v0.10.2 observation above is version-specific evidence,
not a guarantee that a future installer will have identical effects.
