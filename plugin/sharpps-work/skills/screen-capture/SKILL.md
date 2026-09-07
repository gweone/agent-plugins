---
name: screen-capture
description: Use when the user wants a real screenshot of a web app for documentation — mentions "screenshot", "screen capture", "capture the UI", wants a guideline/manual with actual pictures of the app rather than mockups, or asks to document a login/setup/error flow visually. Covers headless-browser capture via Playwright/Chromium, including the specific problem of a local multi-tenant or reverse-proxied instance whose real domain doesn't resolve to the dev/test environment (common for self-hosted apps like Frappe/ERPNext, or any app using Host-header-based virtual hosting) — solved with `--host-resolver-rules`, not Host-header route interception (documented as unreliable). Also covers login automation, session reuse via storageState, selector-robustness pitfalls that cause silently-wrong captures, and iterative screenshot-driven debugging.
---

# Screen capture via headless browser

Real screenshots of a real, running app beat mockups for any "here's what the user actually
sees" documentation. This skill drives a headless Chromium via Playwright to log in, navigate,
and capture — grounded in problems that actually occur (not just the happy path).

**Cross-platform**: Playwright and the `--host-resolver-rules` technique below both work
identically on Windows, macOS, and Linux. The only OS-specific details are the environment-setup
flags/paths noted inline (Linux-only `--with-deps` caveat, hosts-file path, PowerShell vs. bash
credential redirection) — the actual capture logic (login, navigation, screenshots) is the same
JS on every platform.

## Workflow: Spec → Plan → Capture

Never jump straight to writing a capture script.

1. **Spec** — resolve exactly what to capture: which screens/flows, as which user role(s) (a
   restricted view often needs a *different* login than an admin view), and where the target
   app actually lives (URL, port, whether it's local/containerized). Ask the user if the list of
   screens is ambiguous — a vague "document the whole app" produces either too little or an
   unreviewable pile of screenshots.
2. **Plan** — state which login(s) are needed and what credential source each uses (see
   Credentials below), and the ordered list of navigation steps per screenshot, before running
   anything.
3. **Capture** — run it, and *read back every screenshot before moving on* (see Debugging
   below) — a script exiting with status 0 does not mean the screenshot shows what was intended.

## Environment setup

Cross-platform — same two commands on Windows, macOS, and Linux:

```bash
npm install playwright
npx playwright install chromium
```

`--with-deps` is a **Linux-only** convenience flag (installs the OS-level shared libraries
Chromium needs via the system package manager) — it is meaningless on Windows/macOS and should
just be omitted there. On Linux specifically, only add it on Debian/Ubuntu-family systems; on any
other Linux (RHEL/Oracle/Fedora/Alpine, etc.) it shells out to `apt-get`, which doesn't exist, and
fails outright. Plain `install chromium` (no `--with-deps`) still works there: it downloads the
browser binary and (confirmed live, Oracle Linux) launches and renders fine without that OS-level
dependency step.

Smoke-test before building the real capture script:

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

## Login and session reuse

```js
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
await page.fill('#login_email', username);      // selector names vary by app - inspect first
await page.fill('#login_password', password);
await page.click('.btn-login');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000);   // SPAs often finish network activity before finishing
                                    // client-side rendering - a short explicit wait after
                                    // networkidle avoids capturing a half-rendered page

await context.storageState({ path: 'auth_state.json' });
```

Reuse the saved session in later capture scripts instead of logging in again:

```js
const context = await browser.newContext({ storageState: 'auth_state.json' });
```

If multiple roles need documenting (e.g. an admin view and a restricted end-user view), save a
separate storageState file per role/login.

## Credentials

- Never echo a password/secret into any command's visible output or into a script printed to
  the transcript.
- When a credential must be pulled from a remote/containerized environment (e.g. an env var
  inside a Docker container), redirect it straight to a file rather than displaying it, so the
  value never appears in the command's own stdout capture, only in the file the script then
  reads:
  - bash/macOS/Linux: `docker exec container sh -c 'printf "%s" "$SECRET_VAR"' > .secret_file`
  - PowerShell/Windows: `docker exec container sh -c 'printf "%s" "$SECRET_VAR"' | Out-File -NoNewline .secret_file`
    (`Out-File` defaults to UTF-16 and adds a trailing newline — both flags above avoid
    corrupting the value; `Set-Content -NoNewline` is an equivalent alternative)
- Delete any file holding a real credential (and any `storageState.json` containing session
  cookies) once capture is done — these are session artifacts, not deliverables.

## Selector robustness — pitfalls that cause silently-wrong captures

- **Never use a bare `page.click('text=...')` for common words** ("Create", "Save", "Edit") on
  a page with a sidebar/nav — it can match an unrelated element elsewhere on the page and
  navigate somewhere completely different, and the script won't error, it'll just screenshot the
  wrong page. Scope the selector to the actual toolbar/container:
  `page.locator('.page-actions button:has-text("Create")')`.
- **When a locator resolves to multiple elements**, Playwright picks the first — that is *not*
  necessarily the visible/interactive one (dropdown menus commonly render more than one match,
  one hidden). Prefer a selector specific enough to resolve to exactly one element, and add
  `.first()`/`.last()` only as a last resort with an explicit visibility check.
- **In a repeating grid/table**, target rows by an explicit index attribute
  (`[data-idx="1"]` or the app's equivalent), not `.first()`/`.last()` — adding or removing a row
  during the same flow silently shifts what `.last()` now refers to, and a script that "worked"
  can start filling the wrong row after an earlier step changed the row count.
- Generic form-level errors (e.g. "quantity cannot be zero", "field X is mandatory") often fire
  *before* the specific validation actually being documented — if a capture keeps hitting the
  wrong error dialog, check what other mandatory fields the form needs filled first before the
  intended validation path is even reached.

## Debugging workflow

Iterate by capturing a screenshot after every meaningful step and **actually reading it back**
before trusting the script succeeded — a script exiting 0 only means no exception was thrown, not
that the right thing is on screen (a wrong click can silently land on an unrelated page). This is
the fastest way to catch a bad selector, a covering overlay, or a wrong-page navigation.

Useful capture hygiene:
- Widen the viewport (e.g. `{ width: 1920, height: 1000 }`) for data-dense screens like list
  views with many columns, so more fits without needing to scroll-and-stitch.
- Dismiss onboarding/tour popups ("Getting Started" widgets, cookie banners) before the final
  capture of a screen, so the screenshot documents the actual feature, not a widget covering it.
- Save screenshots with a clear ordered naming scheme (`section_NN_description.png`) so they
  drop straight into a document in the right order without manual sorting.
