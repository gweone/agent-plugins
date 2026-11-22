# sharpps-mcp 1.0.0

**SharpPS Replayr** for any AI agent: just the Replayr MCP endpoint, no skills. The server itself sends usage instructions to the agent when it connects (the working loop, secrets, guarded actions), so every MCP client gets them.

- Endpoint: `https://replayr.sharpps.dpdns.org/api/mcp` (Streamable HTTP)
- Sign-in: OAuth (the agent opens a browser the first time) or an API token created under **Tokens** in Replayr
- Same roles as the web app: viewer, editor, admin. Destructive tools need `confirm: true`.

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

### With an API token instead of OAuth

Create a token in Replayr (Tokens page), export it as `REPLAYR_TOKEN` in your shell, and send it as a header. Never put the token itself in a file that is committed.

```json
{ "mcpServers": { "sharpps-replayr": { "type": "http", "url": "https://replayr.sharpps.dpdns.org/api/mcp", "headers": { "Authorization": "Bearer ${REPLAYR_TOKEN}" } } } }
```

### More than one workspace

Add `?workspace=<organization id>` to the URL, or send the header `X-Replayr-Workspace`. A single-workspace account needs neither.

## Self-hosted Replayr

Replace the host in the URL. Nothing else changes.
