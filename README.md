# claude-plugins

A Claude Code plugin marketplace for SharpPS framework tooling and knowledge.

## Structure

- **`/plugin`** - plugins developed and maintained here

## Installation

Add this marketplace, then install a plugin from it:

```
/plugin marketplace add gweone/claude-plugins
/plugin install sharpps-sitecore@sharpps-plugins
/plugin install sharpps-liferay@sharpps-plugins
/plugin install sharpps-dotnet@sharpps-plugins
/plugin install sharpps-work@sharpps-plugins
```

or browse for the plugin in `/plugin > Discover`.

## Plugins

| Plugin | Description |
|---|---|
| [`sharpps-sitecore`](plugin/sharpps-sitecore) | Sitecore/SXA knowledge for solutions built on the SharpPS framework |
| [`sharpps-liferay`](plugin/sharpps-liferay) | Liferay knowledge and workflow tooling for solutions built on the SharpPS framework |
| [`sharpps-dotnet`](plugin/sharpps-dotnet) | .NET tooling knowledge for solutions built on the SharpPS framework |
| [`sharpps-work`](plugin/sharpps-work) | General office/documentation tooling (screen capture, Word document generation) — not tied to any one platform |

## Plugin structure

Each plugin follows the standard Claude Code plugin layout:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (required)
├── skills/               # Skill definitions
└── README.md             # Documentation
```

## Plugin names are immutable

The `name` field in a marketplace entry is an immutable slug - once a plugin
has been published, its `name` must not change. If a rename is genuinely
unavoidable, add an entry to the top-level `renames` map in
`.claude-plugin/marketplace.json` so existing installs auto-migrate.

## Multi-agent support

Skills are **not** duplicated. Canonical tree:

```text
./plugin/<name>/skills/<skill>/SKILL.md
```

Each host package only references that tree:

```text
./plugin/<name>/
  skills/                       # only copy of SKILL.md
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json     # "skills": "./skills/"
  .cursor-plugin/plugin.json    # "skills": "./skills/"
  .grok-plugin/plugin.json      # "skills": "./skills/"
```

| Host | Entry |
|------|--------|
| Claude Code | `/plugin marketplace add gweone/claude-plugins` |
| Codex / ChatGPT | `.agents/plugins/marketplace.json` (`path: ./plugin/<name>`) |
| Cursor | `.cursor-plugin/marketplace.json` |
| Grok | per-plugin `.grok-plugin/plugin.json` |

Do **not** use `.agents/skills` as a skill base.

```bash
./scripts/install-agent-skills.sh
```
