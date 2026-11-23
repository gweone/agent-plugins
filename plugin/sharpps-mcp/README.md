# sharpps-mcp 1.4.1

SharpPS MCP endpoints for any AI agent: **Replayr** (Playwright tests) and **Identity Groups** (Entra-style groups for Clerk). The servers send their own usage instructions when the agent connects, so every MCP client gets them. The plugin ships no skills: any detailed guidance is served by the MCP servers themselves.

| Server | Endpoint | What it does |
|---|---|---|
| `SharpPS Replayr` | `https://replayr.sharpps.dpdns.org/api/mcp` | Write, run and review Playwright tests |
| `SharpPS Groups` | `https://groups.sharpps.dpdns.org/mcp` | List groups and members, find users, add or remove members, create and delete groups |
| `SharpPS Chrome Dev Tools` | `https://cloud.sharpps.dpdns.org/chrome/mcp` | Chrome DevTools tools on the shared SharpPS browser. Needs membership of the Chrome group |
| `SharpPS Shells` | `https://cloud.sharpps.dpdns.org/shell/mcp` | Run shell commands, read and write files, and use persistent shell sessions on the SharpPS Cloud Workstation (the remote server), not in your local shell. Needs membership of the Shell group |
| `SharpPS Attendance` | `https://cloud.sharpps.dpdns.org/attendance/mcp` | Clock in and out and read your attendance record through Talenta, with your own stored login. Needs membership of the Attendance group |
| `SharpPS Trading` | `https://cloud.sharpps.dpdns.org/trading/mcp` | Market screening and analysis tools, plus live Indodax trading and the trading bot. Spends real money: needs membership of the Trading group |

The four `cloud.sharpps.dpdns.org` servers (Chrome, Shells, Attendance, Trading) sign in with Clerk and only let in people who belong to their group in SharpPS Groups. If a server refuses you, ask an administrator to add you there.

## Replayr

- Endpoint: `https://replayr.sharpps.dpdns.org/api/mcp` (Streamable HTTP)
- Sign-in: OAuth (the agent opens a browser the first time). Replayr has no separate API tokens: the agent acts as you, with your Replayr groups
- Same roles as the web app: viewer, editor, admin. Destructive tools need `confirm: true`.

## Identity Groups

- Endpoint: `https://groups.sharpps.dpdns.org/mcp` (Streamable HTTP)
- Sign-in: Clerk OAuth with CIMD, so no client ID is pre-registered. The agent opens a browser the first time and you approve the scopes.
- Scopes decide which tools you see: `me:read` (`my_groups`), `groups:read` (list and read), `groups:write` (add or remove members) and `groups:admin` (create, rename, delete groups, resync). A read-only connection never lists write tools. Changing a group still needs an administrator, or the owner of that group.
- Write tools accept `dry_run: true` to preview the before/after membership. Every call is recorded in the service's audit log with your user and the agent's client ID.

## Install

Claude Code, Codex, Cursor, Grok: install the plugin from this marketplace; the MCP server comes with it.

```
/plugin marketplace add gweone/agent-plugins
/plugin install sharpps-mcp@sharpps-plugins
```

Then authorize the server (`/mcp` in Claude Code) and ask, for example: "Run the login tests on my staging project and tell me what failed."

## Any other agent

Add the endpoint as a remote (HTTP) MCP server in the agent's own settings.

Claude.ai and Claude Desktop: Settings, Connectors, add a custom connector with the URL above.

VS Code (`.vscode/mcp.json`):

```json
{ "servers": { "sharpps-replayr": { "type": "http", "url": "https://replayr.sharpps.dpdns.org/api/mcp" } } }
```

OpenCode (`opencode.json`, already in this repo's root file):

```json
{ "mcp": { "sharpps-replayr": { "type": "remote", "url": "https://replayr.sharpps.dpdns.org/api/mcp", "enabled": true } } }
```

Clients that read `mcpServers` (Windsurf, Cline, Zed and others):

```json
{ "mcpServers": { "sharpps-replayr": { "type": "http", "url": "https://replayr.sharpps.dpdns.org/api/mcp" } } }
```

Gemini CLI: `gemini mcp add --transport http sharpps-replayr https://replayr.sharpps.dpdns.org/api/mcp`

### More than one workspace

Add `?workspace=<organization id>` to the URL, or send the header `X-Replayr-Workspace`. A single-workspace account needs neither.

## Self-hosted Replayr

Replace the host in the URL. Nothing else changes.
