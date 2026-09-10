# agent-plugins

A multi-agent plugin marketplace (Claude Code, Codex/ChatGPT, Cursor, Grok, OpenCode) for SharpPS framework tooling and knowledge.

## Structure

- **`/plugin`** - plugins developed and maintained here

## Installation

Add this marketplace, then install a plugin from it:

```
/plugin marketplace add gweone/agent-plugins
/plugin install sharpps-sitecore@sharpps-plugins
/plugin install sharpps-liferay@sharpps-plugins
/plugin install sharpps-dotnet@sharpps-plugins
/plugin install sharpps-work@sharpps-plugins
```

or browse for the plugin in `/plugin > Discover`.

### OpenCode

OpenCode has no marketplace/install command - it discovers skills directly from
paths listed in an `opencode.json`. If you're working from inside a clone of
this repo, the root [`opencode.json`](opencode.json) already points at every
plugin's `skills/` tree, so nothing further is needed.

To use these skills from another project, clone this repo somewhere (e.g.
`~/agent-plugins`) and add the paths you want to your own `opencode.json`
(project-local or `~/.config/opencode/opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": [
    "~/agent-plugins/plugin/sharpps-sitecore/skills",
    "~/agent-plugins/plugin/sharpps-liferay/skills",
    "~/agent-plugins/plugin/sharpps-dotnet/skills",
    "~/agent-plugins/plugin/sharpps-work/skills"
  ]
}
```

## Plugins

| Plugin | Description |
|-s|---|
| [`sharpps-sitecore`](plugin/sharpps-sitecore) | Sitecore/SXA knowledge for solutions built on the SharpPS framework |
| [`sharpps-liferay`](plugin/sharpps-liferay) | Liferay knowledge and workflow tooling for solutions built on the SharpPS framework |
| [`sharpps-dotnet`](plugin/sharpps-dotnet) | .NET tooling knowledge for solutions built on the SharpPS framework |
| [`sharpps-work`](plugin/sharpps-work) | General office/documentation tooling (screen capture, Word document generation) — not tied to any one platform |

## Plugin structure

Each plugin follows the standard Claude Code plugin layout as its canonical source — every other host (Codex, Cursor, Grok, OpenCode) references the same `skills/` tree rather than duplicating it:

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
  .opencode-plugin/plugin.json  # "skills": "./skills/" (reference only, see below)
```

| Host | Entry |
|------|--------|
| Claude Code | `/plugin marketplace add gweone/agent-plugins` |
| Codex / ChatGPT | `.agents/plugins/marketplace.json` (`path: ./plugin/<name>`) |
| Cursor | `.cursor-plugin/marketplace.json` |
| Grok | per-plugin `.grok-plugin/plugin.json` |
| OpenCode | root [`opencode.json`](opencode.json) `skills` array → `./plugin/<name>/skills` |

Do **not** use `.agents/skills` as a skill base.

Note on OpenCode specifically: OpenCode has no plugin/marketplace-install
concept and never parses a `plugin.json`. Each plugin's `.opencode-plugin/plugin.json`
exists only for documentation/consistency with the other host folders. The
thing OpenCode actually reads is the `skills` array in `opencode.json` (see
[Installation](#installation) above) or its own native skill-discovery paths
(`.opencode/skills/`, `.claude/skills/`, `.agents/skills/`) — we intentionally
don't populate those native paths here, to keep a single canonical skills tree
per the no-duplication rule.

```bash
./scripts/install-agent-skills.sh
```
