# Setup: Chrome DevTools MCP

Check first: if tools such as `list_pages`, `take_snapshot`, and
`list_console_messages` are already in the tool list, setup is done. Installing or
registering a server changes the user's agent configuration; ask before doing it.

## Requirements

- Node.js LTS and npm.
- Current stable Chrome (or newer). The server starts the browser lazily on the first
  tool call, not when the client connects.

## Register the server

The server is the same on every host: the command `npx` with args
`-y chrome-devtools-mcp@latest`. Only where and how each host stores it differs.
Detect which agent host you are running in and use its row; if unsure, ask the user.

Generic JSON shape (Claude Code `.mcp.json`, Cursor, Gemini CLI, and most clients):

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### Per-host registration

Paths and commands change between host versions; confirm against the host's current MCP
docs or `<host> mcp --help` before writing config. Upstream keeps a per-client guide:
https://github.com/ChromeDevTools/chrome-devtools-mcp (see "MCP Client configuration").

| Host | Project scope | Global (user) scope |
|---|---|---|
| Claude Code | `claude mcp add --scope project chrome-devtools -- npx -y chrome-devtools-mcp@latest` (writes `.mcp.json`) | `claude mcp add --scope user chrome-devtools -- npx -y chrome-devtools-mcp@latest` (`~/.claude.json`); default scope is local, this project and you only |
| Codex | `.codex/config.toml` in a trusted project | `codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest`, or `~/.codex/config.toml` (TOML below) |
| Cursor | `.cursor/mcp.json` (generic JSON above) | `~/.cursor/mcp.json` (generic JSON above) |
| OpenCode | `opencode.json` in the project (OpenCode shape below) | `~/.config/opencode/opencode.json` |
| VS Code / Copilot | `.vscode/mcp.json` (top-level key is `servers`, not `mcpServers`) | user profile `mcp.json` via "MCP: Open User Configuration" |
| Gemini CLI | `.gemini/settings.json` | `gemini mcp add chrome-devtools npx chrome-devtools-mcp@latest`, or `~/.gemini/settings.json` |
| Grok / others | host's project MCP config | host's user MCP config; use the same `command` and `args` |

Codex TOML:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest"]
```

OpenCode shape (command is a single array and the entry needs a `type`):

```json
{
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

Windows: some hosts cannot spawn `npx` directly; use `"command": "cmd"` with
`"args": ["/c", "npx", "-y", "chrome-devtools-mcp@latest"]`.

### Project vs. global

- Project scope is shared with the team through git; pin a version there.
- Global scope is a machine-wide change to the user's agent configuration. Ask before
  doing it, and add `--isolated` to the args so every project doesn't share one
  persistent profile with saved logins.
- Verify with the host's list command (`claude mcp list`, `codex mcp list`,
  `gemini mcp list`) or its MCP settings UI. Remove with the host's `mcp remove`.

Restart the client afterwards; tools do not appear mid-session. For reproducible CI or
shared setups pin a version instead of `@latest`.

Smoke test: ask for `list_pages`, then `navigate_page` to a known URL and
`take_snapshot`.

## Useful flags

Append to `args`. Confirm against `npx chrome-devtools-mcp@latest --help`, since flags
change between versions.

| Flag | Use |
|---|---|
| `--headless` | No visible window (servers, CI). |
| `--isolated` | Throwaway profile, so no saved logins leak in and nothing persists. |
| `--browserUrl <url>` | Attach to Chrome already started with `--remote-debugging-port`. |
| `--wsEndpoint <ws>` | Attach via a WebSocket endpoint. |
| `--autoConnect` | Attach to a running Chrome with remote debugging enabled (see below). |
| `--channel <name>` | Pick stable, beta, dev, or canary. |
| `--viewport WxH` | Initial viewport size. |
| `--slim` | Reduced tool set for basic browsing only; the debugging tools are gone. |
| `--categoryExtensions` | Extension tools (install/list/trigger). |
| `--memoryDebugging` | Heap snapshot tools. |
| `--no-performance-crux` | Don't send URLs to the CrUX API for field data. |
| `--no-usage-statistics` | Opt out of usage statistics (on by default). |

Defaults to know: a persistent profile is reused between runs. Use `--isolated` unless
you need an existing login.

## Debugging a page the user already has open (their login)

1. Start Chrome with `--remote-debugging-port=9222` (and a separate
   `--user-data-dir`), then use `--browserUrl http://127.0.0.1:9222`.
2. Or enable remote debugging at `chrome://inspect/#remote-debugging` and use
   `--autoConnect`.

Anything reachable on that port can control the browser. Bind to localhost only and
close it when done.

## Linux / headless hosts

Chrome must be installed and launchable. If it fails to start, check for missing shared
libraries and for sandbox restrictions in containers. Use `--headless` and `--isolated`.

## Troubleshooting connection errors

- `list_pages`/`new_page`/`navigate_page` fail or the server won't start: read the MCP
  config for bad args or `--autoConnect` in an unsupported environment.
- `Could not find DevToolsActivePort`: only applies to `--autoConnect`. Confirm the
  right Chrome is running and that remote debugging is enabled at
  `chrome://inspect/#remote-debugging`, then retry `list_pages` before changing config.
- Server starts but shows an empty profile: check flag typos (`--browserUrl` vs
  `--browser-url`).
- Upstream guide: https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/troubleshooting.md
- The package also ships a `chrome-devtools` CLI and companion skills (`a11y-debugging`,
  `cookie-debugging`, `debug-optimize-lcp`, `memory-leak-debugging`,
  `troubleshooting`); install them from the upstream repo if the user wants them.
