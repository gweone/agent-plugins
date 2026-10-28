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

## Browser mode: isolated (default) or existing Chrome (optional)

Pick one mode per registration; the server reads its args at start-up only.

| Mode | Args | Sees | Use when |
|---|---|---|---|
| Isolated (default) | `--isolated` | Fresh throwaway Chrome, no logins | Public pages, test accounts, safest |
| Existing Chrome | `--autoConnect` | The user's running Chrome: every window, tab, and profile, with live logins | Bug only reproduces in the user's session |
| Dedicated debug Chrome | `--browserUrl http://127.0.0.1:9222` | A second Chrome with its own `--user-data-dir` | Persistent test login without exposing the daily profile |

Existing Chrome is opt-in only: the user must ask for it. Explain first that the agent
can then read and drive every tab and session in that browser.

### Existing Chrome via `--autoConnect` (Chrome 144+)

1. User enables remote debugging at `chrome://inspect/#remote-debugging`. The page
   shows `Server running at: 127.0.0.1:<port>`.
2. Register with `--autoConnect` (drop `--isolated`), e.g. Claude Code on Windows:
   `claude mcp add --scope user chrome-devtools -- cmd /c npx -y chrome-devtools-mcp@latest --autoConnect`
   (remove the old entry first with `claude mcp remove chrome-devtools -s user`).
3. The user restarts the client; a reload of the current session is not enough.
4. On first connect Chrome shows an allow-debugging prompt; the user clicks **Allow**.

Facts to know:

- The port is discovered automatically: the server reads the `DevToolsActivePort` file
  in the stable channel's default user data dir. The user does not need to say the port.
  Other channels (Beta/Canary) need `--channel`.
- This toggle mode does not serve the HTTP endpoints: `GET /json/version` returns 404.
  That is expected; it means use `--autoConnect`, not `--browserUrl`.
- The toggle is per browser instance; after fully quitting Chrome, expect to re-enable it.
- Since Chrome 136, `--remote-debugging-port` is ignored on the default profile, so the
  command-line route requires a separate `--user-data-dir` (the dedicated mode above).

### Dedicated debug Chrome via `--browserUrl`

Start Chrome with `--remote-debugging-port=9222 --user-data-dir=<separate dir>` (a
desktop shortcut works), log in once, then register with
`--browserUrl http://127.0.0.1:9222`. No toggle or Allow prompt each time.

Anything reachable on the debugging port can control the browser. Bind to localhost
only and turn it off when done.

### Choosing the tab when attached

1. `list_pages` shows all tabs across every window and profile.
2. Pick the tab whose URL matches the user's target; if several match or none is clear,
   ask. If the page isn't open, `new_page` rather than navigating a tab the user is using.
3. Read and act only in the chosen tab; leave unrelated tabs (mail, banking) alone.

### Verify which mode is actually running

Config changes don't affect a running session. If `list_pages` shows only
`about:blank` while the user expects their tabs, the old server is still running. Check
its args (Windows: `Get-CimInstance Win32_Process | ? CommandLine -match 'chrome-devtools-mcp'`;
elsewhere `ps aux | grep chrome-devtools-mcp`) and ask the user to restart the client.

## Linux / headless hosts

Chrome must be installed and launchable. If it fails to start, check for missing shared
libraries and for sandbox restrictions in containers. Use `--headless` and `--isolated`.

## Troubleshooting connection errors

- `list_pages`/`new_page`/`navigate_page` fail or the server won't start: read the MCP
  config for bad args or `--autoConnect` in an unsupported environment.
- `Could not find DevToolsActivePort`: only applies to `--autoConnect`. Confirm the
  right Chrome is running and that remote debugging is enabled at
  `chrome://inspect/#remote-debugging`, then retry `list_pages` before changing config.
- `--browserUrl` fails but `chrome://inspect` says the server is running: the toggle
  mode has no `/json/version` (404). Switch to `--autoConnect`.
- Only `about:blank` after switching to `--autoConnect`: the client wasn't restarted;
  see "Verify which mode is actually running".
- Server starts but shows an empty profile: check flag typos (`--browserUrl` vs
  `--browser-url`).
- Upstream guide: https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/troubleshooting.md
- The package also ships a `chrome-devtools` CLI and companion skills (`a11y-debugging`,
  `cookie-debugging`, `debug-optimize-lcp`, `memory-leak-debugging`,
  `troubleshooting`); install them from the upstream repo if the user wants them.
