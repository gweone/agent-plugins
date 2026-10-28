# Setup: Chrome DevTools MCP

Check first: if tools such as `list_pages`, `take_snapshot`, and
`list_console_messages` are already in the tool list, setup is done. Installing or
registering a server changes the user's agent configuration; ask before doing it.

## Requirements

- Node.js LTS and npm.
- Current stable Chrome (or newer). The server starts the browser lazily on the first
  tool call, not when the client connects.

## Register the server

Add to the MCP client config (project `.mcp.json`, or the client's equivalent):

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

Claude Code one-liner: `claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest`

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
