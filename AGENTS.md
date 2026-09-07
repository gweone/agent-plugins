# SharpPS Agent Skills

Shared SharpPS workflow skills for Claude Code, Codex, ChatGPT, Cursor, Grok, and other agents.

## Canonical layout (single source of truth)

```text
./plugin/<plugin-name>/skills/<skill-name>/SKILL.md
```

Examples:

```text
./plugin/sharpps-sitecore/skills/sxa-search/SKILL.md
./plugin/sharpps-dotnet/skills/decompile-dll/SKILL.md
```

There is **no** skill root at `.agents/skills`. That path is not used.

## How each host finds skills

| Host | How |
|------|-----|
| Claude Code | `.claude-plugin/marketplace.json` → `source: ./plugin/<name>` |
| Codex / ChatGPT | `.agents/plugins/marketplace.json` → local `path: ./plugin/<name>`; per-plugin `.codex-plugin` has `skills: "./skills/"` |
| Cursor | `.cursor-plugin/marketplace.json` + per-plugin `.cursor-plugin` → `skills: "./skills/"` |
| Grok | per-plugin `.grok-plugin` → `skills: "./skills/"` |

Relative to each plugin package root (`./plugin/<name>`), the skills directory is always **`./skills/`**.

## Rules

- Edit only files under `./plugin/*/skills/`.
- Do not copy `SKILL.md` into `.codex-plugin`, `.cursor-plugin`, `.grok-plugin`, or `.agents/`.
- Provider folders only hold `plugin.json` manifests that **reference** `./skills/`.
- User instructions override skill guidance.

## Validation

```bash
./scripts/install-agent-skills.sh
```
