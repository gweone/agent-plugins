# Playwright setup and local-domain routing

## Environment setup

With user authorization to install dependencies in the chosen environment, use these commands on Windows, macOS, and Linux:

```bash
npm install playwright
npx playwright install chromium
```

`--with-deps` is a **Linux-only** convenience flag (installs the OS-level shared libraries
Chromium needs via the system package manager) — it is meaningless on Windows/macOS and should
just be omitted there. On Linux specifically, only add it on Debian/Ubuntu-family systems; on any
other Linux (RHEL/Oracle/Fedora/Alpine, etc.) it shells out to `apt-get`, which doesn't exist, and
fails outright. Plain `install chromium` (no `--with-deps`) downloads the browser without that OS-level
dependency step; a successful launch still depends on compatible installed libraries and a
supported browser/platform combination. Diagnose missing libraries rather than assuming it works.

After setup is authorized, smoke-test before building the real capture script:

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

## Reaching a local multi-tenant / reverse-proxied instance

Many self-hosted apps (Frappe/ERPNext multi-site, and generally anything using Host-header-based
virtual hosting) route requests to the correct tenant/site purely by the `Host` header — the app
running on `localhost:PORT` will reject a request whose Host header says `localhost` with a
generic "site not found" error. The real domain (e.g. `myapp.example.com`) usually has its own
DNS pointing at a *different*, real server — not your local/dev instance — so navigating to it
directly connects to the wrong place entirely.

**Do not** try to fix this via request interception (`context.route(...)` rewriting the `host`
header before `route.continue()`) — confirmed unreliable: Chromium's network stack does not
consistently honor a rewritten Host header for navigation requests, and the app still sees
`localhost`/whatever the original authority was.

**Do** launch Chromium with a host-resolver rule that maps the real hostname straight to the
local instance's IP, then navigate using that real hostname (so the Host header is naturally
correct — no interception needed at all). This is a Chromium engine flag, not an OS feature, so
it works identically on Windows, macOS, and Linux:

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

If unsure why direct navigation is timing out/hanging, check the OS hosts file for a real public
domain entry pointing elsewhere (the usual tell) — `/etc/hosts` on macOS/Linux,
`C:\Windows\System32\drivers\etc\hosts` on Windows (needs an elevated/Administrator editor to
modify, though this skill only needs to *read* it to diagnose, not edit it).

