# Setup: Playwright CLI

Check first: `playwright-cli --version` (or `--help`). If it works, setup is done.
Global installs and browser downloads need user authorization.

## Requirements

- Node.js 18 or newer.
- A browser. Playwright can download its own; `--browser=chrome` uses installed Chrome.

## Install

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

`-g` installs the CLI for every project on the machine (a global change, so ask first).
It is a shell command, not an MCP server, so nothing needs registering in any agent's
config; every host that can run shell commands can use it. For an MCP-style setup use
Playwright MCP instead (`npx @playwright/mcp@latest`, registered like the
Chrome DevTools server in the `browser-debug` skill's setup reference), but the CLI
is the lighter option for coding agents.

Without a global install: `npx @playwright/cli@latest --help`; substitute that for
`playwright-cli` in every command. Pin a version for reproducible QA runs.

Browsers, if the CLI reports none installed:

```bash
npx playwright install chromium
# Linux hosts missing system libraries (needs root; ask first):
npx playwright install --with-deps chromium
```

Optional: `playwright-cli install --skills` writes the upstream skill into the project
so agents pick it up. This changes the workspace, so ask first. This plugin's skill
works without it.

## Smoke test

```bash
playwright-cli -s=smoke open https://example.com
playwright-cli -s=smoke snapshot
playwright-cli -s=smoke screenshot --filename=smoke.png
playwright-cli -s=smoke close
```

Confirm a snapshot file and `smoke.png` exist and show the expected page. Snapshots and
default outputs go under `.playwright-cli/` in the current directory. Add it to
`.gitignore`, and run from a scratch or agreed directory.

## Modes

- Headless is the default; add `--headed` to `open` to watch it run.
- Profile is in memory by default; `--persistent` or `--profile=<path>` writes it to disk
  (sensitive when logged in).
- `playwright-cli show` opens a dashboard of live sessions.
- `attach --cdp=<url|chrome>` or `attach --extension=chrome` drives an already-running
  browser; only on the user's explicit say-so, since it exposes their real sessions.
- A headless session closes itself after an hour idle (`--idle-timeout=<ms>`, `0`
  disables).

## Local virtual hosts

If the app's real hostname doesn't resolve on this machine, a Chromium resolver rule is
the dependable fix (`--host-resolver-rules`; see the `screen-capture` skill). Use
`--config=file.json` or `run-code` to pass launch options; check
`playwright-cli open --help` for what your version supports. Don't use Host-header route
interception.

## Test runner (optional)

For committed specs, the project needs `@playwright/test`
(`npm init playwright@latest` scaffolds config; ask first). Run with
`PLAYWRIGHT_HTML_OPEN=never npx playwright test` so no report server blocks the shell.

## Cleanup

`playwright-cli close-all`; if a browser hangs, `kill-all`. `delete-data` removes a
session's stored profile.
