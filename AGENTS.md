# SharpPS Agent Skills

Shared SharpPS workflow skills for Claude Code, Codex, ChatGPT, Cursor, Grok, OpenCode, and other agents.

## Canonical layout (single source of truth)

```text
./plugin/<plugin-name>/skills/<skill-name>/SKILL.md
```

Examples:

```text
./plugin/sharpps-sitecore/skills/sxa-search/SKILL.md
./plugin/sharpps-dotnet/skills/decompile-dll/SKILL.md
```

There is **no** skill root at `.agents/skills`. That path is not used, even
though OpenCode natively scans it — see the OpenCode row below for why.

## How each host finds skills

| Host | How |
|------|-----|
| Claude Code | `.claude-plugin/marketplace.json` → `source: ./plugin/<name>` |
| Codex / ChatGPT | `.agents/plugins/marketplace.json` → local `path: ./plugin/<name>`; per-plugin `.codex-plugin` has `skills: "./skills/"` |
| Cursor | `.cursor-plugin/marketplace.json` + per-plugin `.cursor-plugin` → `skills: "./skills/"` |
| Grok | per-plugin `.grok-plugin` → `skills: "./skills/"` |
| OpenCode | root `opencode.json` → `skills: ["./plugin/<name>/skills", ...]`; per-plugin `.opencode-plugin/plugin.json` is documentation only (OpenCode never parses `plugin.json`) |

Relative to each plugin package root (`./plugin/<name>`), the skills directory is always **`./skills/`**.

OpenCode is the odd one out: it has no marketplace/plugin-install concept and
no `plugin.json` support at all. It discovers skills either via its own fixed
native paths (`.opencode/skills/`, `.claude/skills/`, `.agents/skills/`, each
project- and global-scoped) or via an explicit `skills` array in
`opencode.json`. We deliberately use the latter (root `opencode.json`) instead
of populating `.agents/skills/` with per-skill symlinks, so the canonical tree
stays the single copy and every other host's `.agents/` usage (the Codex
marketplace) stays unambiguous.

## Rules

- Edit only files under `./plugin/*/skills/`.
- Do not copy `SKILL.md` into `.codex-plugin`, `.cursor-plugin`, `.grok-plugin`, `.opencode-plugin`, or `.agents/`.
- Provider folders only hold `plugin.json` manifests that **reference** `./skills/`.
- User instructions override skill guidance.

## Validation

```bash
./scripts/install-agent-skills.sh
```
