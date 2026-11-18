# Setup: Playwright for browser automation

Two ways to drive the browser, both fresh and isolated:

- **`playwright-cli`**: interactive and exploratory checks, QA runs. Keeps page data on
  disk instead of in the context window.
- **Playwright library scripts** (`require('playwright')`): repeatable, scripted captures
  with several roles and many images.

Check first: `playwright-cli --version` (or `--help`), and `node -e "require('playwright')"`
in the project. If what you need works, setup is done. Installs, global changes and browser
downloads need user authorization, in the environment the user chose.

## Requirements

- Node.js 18 or newer.
- A browser. Playwright can download its own; `--browser=chrome` uses installed Chrome.

## Install the CLI

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

`-g` installs the CLI for every project on the machine (a global change, so ask first).
It is a shell command, not an MCP server, so nothing needs registering in any agent's
config; every host that can run shell commands can use it. For an MCP-style setup use
Playwright MCP instead (`npx @playwright/mcp@latest`, registered like the Chrome DevTools
server in the `browser-debug` skill's setup reference), but the CLI is the lighter option
for coding agents.

Without a global install: `npx @playwright/cli@latest --help`; substitute that for
`playwright-cli` in every command. Pin a version for reproducible QA runs.

Optional: `playwright-cli install --skills` writes the upstream skill into the project so
agents pick it up. This changes the workspace, so ask first. This plugin's skill works
without it.

## Install Playwright for scripts

```bash
npm install playwright
npx playwright install chromium
```

Works the same on Windows, macOS and Linux.

## Browsers and Linux libraries

If the CLI or a script reports no browser installed:

```bash
npx playwright install chromium
```

`--with-deps` is a **Linux-only** convenience flag (it installs the OS-level shared
libraries Chromium needs via the system package manager, so it needs root; ask first). It
is meaningless on Windows and macOS, so omit it there. On Linux, only add it on
Debian/Ubuntu-family systems; on any other Linux (RHEL, Oracle, Fedora, Alpine, ...) it
shells out to `apt-get`, which does not exist, and fails outright. Plain
`install chromium` downloads the browser without that step; a successful launch still
depends on compatible installed libraries and a supported browser/platform combination.
Diagnose missing libraries rather than assuming it works.

## Using an installed Chrome or Edge

Playwright can launch the browser already installed on the machine instead of its bundled
Chromium:

```bash
playwright-cli -s=qa open https://app.example.test --browser=chrome   # or msedge
```

```js
const browser = await chromium.launch({ channel: 'chrome' });          // or 'msedge'
// or an exact binary: chromium.launch({ executablePath: '/path/to/chrome' })
```

- This starts a **new, separate** Chrome process with a clean temporary profile. It is not
  the user's running Chrome and has none of their logins or tabs, so it stays isolated.
  Reaching their real, running Chrome is a different thing (`attach --cdp`, see CLI modes
  below) and needs their explicit say-so.
- Use it when the installed branded Chrome matters (a specific Chrome version, media
  codecs the bundled Chromium lacks, or a managed enterprise setup). Otherwise the bundled
  Chromium is the more reproducible default.
- If the channel is not installed, launch fails with a "could not find executable" error.
  `npx playwright install chrome` installs Google Chrome stable (a system-level change on
  Linux: needs root, so ask first), or use the bundled Chromium instead.

## Smoke tests

CLI:

```bash
playwright-cli -s=smoke open https://example.com
playwright-cli -s=smoke snapshot
playwright-cli -s=smoke screenshot --filename=smoke.png
playwright-cli -s=smoke close
```

Confirm a snapshot file and `smoke.png` exist and show the expected page. Snapshots and
default outputs go under `.playwright-cli/` in the current directory. Add it to
`.gitignore`, and run from a scratch or agreed directory.

Script:

```js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('data:text/html,<h1>hello</h1>');
  await page.screenshot({ path: 'smoke.png' });
  await browser.close();
})();
```

Smoke-test before building the real script.

## CLI modes

- Headless is the default; add `--headed` to `open` to watch it run.
- Profile is in memory by default; `--persistent` or `--profile=<path>` writes it to disk
  (sensitive when logged in).
- `playwright-cli show` opens a dashboard of live sessions.
- `attach --cdp=<url|chrome>` or `attach --extension=chrome` drives an already-running
  browser; only on the user's explicit say-so, since it exposes their real sessions.
- A headless session closes itself after an hour idle (`--idle-timeout=<ms>`, `0` disables).

## Reaching a local multi-tenant or reverse-proxied instance

Many self-hosted apps (Frappe/ERPNext multi-site, and generally anything using
Host-header-based virtual hosting) route requests to the correct tenant/site purely by the
`Host` header. The app running on `localhost:PORT` will reject a request whose Host header
says `localhost` with a generic "site not found" error. The real domain
(e.g. `myapp.example.com`) usually has its own DNS pointing at a *different*, real server,
not your local/dev instance, so navigating to it directly connects to the wrong place.

**Do not** try to fix this with request interception (`context.route(...)` rewriting the
`host` header before `route.continue()`): confirmed unreliable. Chromium's network stack
does not consistently honor a rewritten Host header for navigation requests, and the app
still sees `localhost` or whatever the original authority was.

**Do** launch Chromium with a host-resolver rule that maps the real hostname straight to the
local instance's IP, then navigate using that real hostname (so the Host header is
naturally correct; no interception at all). This is a Chromium engine flag, not an OS
feature, so it works identically on Windows, macOS and Linux:

```js
const SITE_HOST = 'myapp.example.com';
const LOCAL_IP = '127.0.0.1';   // or the container's IP if not localhost
const PORT = 5200;

const browser = await chromium.launch({
  args: [`--host-resolver-rules=MAP ${SITE_HOST} ${LOCAL_IP}`],
});
const page = await browser.newPage();
await page.goto(`http://${SITE_HOST}:${PORT}/login`);
```

For the CLI, pass launch options with `--config=file.json` or `run-code`; check
`playwright-cli open --help` for what your version supports.

If direct navigation times out or hangs, check the OS hosts file for a real public domain
entry pointing elsewhere (the usual tell): `/etc/hosts` on macOS/Linux,
`C:\Windows\System32\drivers\etc\hosts` on Windows. Only *read* it to diagnose; do not edit
it without the user's approval.

## Test runner (optional)

For committed specs, the project needs `@playwright/test` (`npm init playwright@latest`
scaffolds config; ask first). Run with `PLAYWRIGHT_HTML_OPEN=never npx playwright test` so
no report server blocks the shell.

## Cleanup

`playwright-cli close-all`; if a browser hangs, `kill-all`. `delete-data` removes a
session's stored profile.
