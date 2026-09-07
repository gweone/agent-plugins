# claude-plugins

A Claude Code plugin marketplace for SharpPS framework tooling and knowledge.

## Structure

- **`/plugins`** - plugins developed and maintained here

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
| [`sharpps-sitecore`](plugins/sharpps-sitecore) | Sitecore/SXA knowledge for solutions built on the SharpPS framework |
| [`sharpps-liferay`](plugins/sharpps-liferay) | Liferay knowledge and workflow tooling for solutions built on the SharpPS framework |
| [`sharpps-dotnet`](plugins/sharpps-dotnet) | .NET tooling knowledge for solutions built on the SharpPS framework |
| [`sharpps-work`](plugins/sharpps-work) | General office/documentation tooling (screen capture, Word document generation) — not tied to any one platform |

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

## ChatGPT and Codex

The marketplace is also packaged for OpenAI's plugin/skills system. The same `SKILL.md` files are reused so Claude Code, Codex, and ChatGPT do not maintain separate copies of the SharpPS knowledge.

- **Codex marketplace:** `.agents/plugins/marketplace.json`
- **Repo Agent Skills:** `.agents/skills/`
- **Canonical skills:** `plugins/*/skills/*/SKILL.md`
- **Codex/ChatGPT repo guidance:** `AGENTS.md`

Validate the shared skill layout with:

```bash
./scripts/install-agent-skills.sh --check
```

For a ChatGPT/Codex workspace, an administrator can import this GitHub repository from **Workspace settings → Plugins → Add → Import marketplace**. Use the repository root as the marketplace path; the supported Codex marketplace manifest is `.agents/plugins/marketplace.json`.
