# Script generation: gap-free automation scripts

Use a script when a flow must run the same way every time: many steps, several roles, a
regression check, or documentation captures. For one-off exploration use `playwright-cli`
interactively first, then turn what you learned (selectors, the API call behind each click)
into a script. Each `playwright-cli` command is a separate process, so it is not the tool
for a flow where every action must wait for the previous one's result.

## Engine

Scripts run on **Node.js** with the `playwright` package, and nothing else: no PowerShell, no
launcher. `node flow.js` also detects the default browser. (Playwright has Python, .NET and
Java APIs too, but this skill standardizes on Node so that `playwright-cli`, the helpers and
the flows share one engine. A Windows machine needs only Node.)

## Requirements and how each is met

| Requirement | Mechanism |
|---|---|
| Use the current default browser | `launch()` calls `detect-browser.js`, which reads the OS default (Windows registry, macOS LaunchServices, Linux `xdg-settings` / `xdg-mime`). Chrome and Edge run as the installed browser (channel); Brave, Vivaldi and Opera run by executable path; Firefox and Safari run as Playwright's own Firefox and WebKit builds (it cannot drive the installed ones); an unknown or undetected default falls back to bundled Chromium with a warning. `AUTOMATION_BROWSER` overrides |
| Act only after a page has loaded or navigated | `goto()` waits for `domcontentloaded`, then the `ready` elements, then network quiet. A click that navigates uses `navigates` |
| Confirm every click or event | `responses` (the API call the click triggers), `visible` / `hidden` / `text` (the element change), `navigates` (the URL) |
| Confirm ready before the next action | `ready` (what the next step needs) plus the network-quiet check |
| Wait for backend and API calls | `responses` with `status` and `body` checks, armed before the click; follow-up calls named explicitly |
| No gap between steps | Every step is arm → act → confirm → quiet → ready. Every wait has a timeout and a named failure. No fixed sleeps |

Detection chooses the browser *type*. Playwright always starts a **new process with a clean
temporary profile**: the user's logins, tabs and extensions are not used. Reaching their
running browser is a separate matter that needs their explicit say-so ([setup](setup.md)).

## Files in `scripts/`

- `steps.js`: `launch`, `step`, `goto`, `waitQuiet`, `close`. `launch()` starts the detected browser.
- `detect-browser.js`: no dependencies; `node detect-browser.js` prints the browser it would choose
  (`{ os, source, rawId, id, engine, channel, executablePath, note }`).

Copy both next to the flow (`require('./steps')`), then:

```bash
npm install playwright                                   # in the project
node ./flow.js                                           # runs in the detected default browser
AUTOMATION_BROWSER=msedge HEADED=1 node ./flow.js        # override the browser, show it
node ./detect-browser.js                                 # what would be chosen
```

| Variable | Meaning |
|---|---|
| `AUTOMATION_BROWSER` | Use this browser instead of the detected default (`chrome`, `msedge`, `firefox`, `safari`, `brave`, `vivaldi`, `opera`, `chromium`) |
| `PW_ENGINE` / `PW_CHANNEL` / `PW_EXECUTABLE` | Pin the browser exactly (`chromium`, `firefox`, `webkit` / `chrome`, `msedge` / a binary path) and skip detection |
| `PW_FALLBACK=0` | Fail instead of falling back to bundled Chromium |
| `HEADED=1` | Show the browser |
| `EVIDENCE_DIR` | Where failure screenshots go (default `evidence`) |
| `STEP_TIMEOUT` / `STEP_QUIET_MS` | Default per-wait limit (15000 ms) / quiet window (300 ms) |

If the chosen browser cannot be launched (the Playwright Firefox build is not installed, Chrome
is not at its expected path), `launch()` warns loudly and falls back to bundled Chromium. The
evidence then comes from a different browser, so say so in the report. Use `PW_FALLBACK=0` when
that is not acceptable.

## The step contract

```js
await step(ctx, 'save item', {
  act: async () => { /* fill, click */ },
  responses: [{ url: '/api/items', method: 'POST', status: 201, body: (j) => j.ok }],
  visible: [page.getByRole('status').filter({ hasText: 'Saved' })],
  ready: [page.getByRole('button', { name: 'New item' })],
});
```

| Field | Meaning |
|---|---|
| `act` | Async function that performs the action (required). It must finish within the timeout |
| `responses` | `[{ url, method, status, body }]`: calls that must complete. `url` is a substring or a regex; `status` defaults to any 2xx; `body` checks the parsed JSON |
| `navigates` | URL (string or regex) the page must reach |
| `visible` / `hidden` | Locators that must be shown / gone (spinners, dialogs) |
| `text` | `[{ locator, text }]`: the locator must contain the text |
| `ready` | Locators the next step needs |
| `quietMs` | No request in flight and none new for this long (default 300; `0` skips) |
| `timeout` | Per-wait limit in ms |

Waiters for `responses` and `navigates` are armed **before** `act` runs, so a fast response
is never missed. On failure the step throws with its name, what it was waiting for, what was
already confirmed, requests in flight, failed requests, console errors, and the path of a
screenshot; the flow exits non-zero.

## Flow template

Placeholder selectors; adapt them to the target app.

```js
const { launch, close, step, goto } = require('./steps');
const BASE = process.env.BASE_URL;                       // credentials come from the environment too

(async () => {
  const ctx = await launch();
  const { page } = ctx;
  try {
    await goto(ctx, `${BASE}/login`, { ready: [page.getByLabel('Email')] });

    await step(ctx, 'sign in', {
      act: async () => {
        await page.getByLabel('Email').fill(process.env.APP_USER);
        await page.getByLabel('Password').fill(process.env.APP_PASSWORD);
        await page.getByRole('button', { name: 'Sign in' }).click();
      },
      responses: [{ url: '/api/session', method: 'POST', status: 200 }],   // the call behind the click
      navigates: /\/dashboard$/,
      ready: [page.getByRole('heading', { name: 'Dashboard' })],
    });

    await step(ctx, 'create item', {
      act: async () => {
        await page.getByLabel('Name').fill('Test item');
        await page.getByRole('button', { name: 'Save' }).click();
      },
      responses: [
        { url: '/api/items', method: 'POST', status: 201 },
        { url: '/api/items', method: 'GET' },              // the list refresh the page fires afterwards
      ],
      text: [{ locator: page.getByRole('table'), text: 'Test item' }],
    });
    console.log('FLOW PASSED');
  } finally {
    await close(ctx);
  }
})().catch((e) => { console.error(e.message); process.exit(1); });
```

## Rules for generating a script

1. Start from the spec: scenarios, expected results, roles, test data, target URL. Explore
   the app with `playwright-cli` first to learn the selectors and the API call behind each
   action, then write the script.
2. One step per user-visible action. **A step without a confirmation is a gap**; only pure
   reads may omit one.
3. Name what each action triggers: the API call (`responses`), the element that changes
   (`visible`, `hidden`, `text`) or the page it reaches (`navigates`). Confirm by content, not
   only by URL: a step can land on the wrong screen with a plausible URL.
4. Name follow-up calls the page fires after an action (list refreshes, re-fetches). The
   quiet check is a safety net, not a substitute: a request that starts more than `quietMs`
   after the previous one is missed (in testing, a refresh fired 400 ms later slipped past a
   300 ms window, and the list was still stale).
5. No fixed sleeps and no `networkidle` as the only wait. Use `ready` and `responses`.
6. Prefer role, label and text locators over CSS paths. Scope them to the right container
   ([screenshot capture](screenshot-capture.md) lists the selector pitfalls).
7. Take credentials from the environment or an approved source; never write them into the
   script or its output ([auth and state](auth-and-state.md)).
8. Dry-run against the target before relying on it, and never run write actions against a
   production-like target without approval.
9. Close the browser in `finally`; keep the exit code non-zero on failure.
10. Report which browser actually ran, including a fallback.

## What was tested

Tested on Oracle Linux 9 (aarch64) with Node 24, Playwright 1.65.1 and bundled Chromium.
Step behavior was tested on a local demo app with slow APIs, a spinner, a delayed follow-up
request, a 500 response and an endpoint that never answers: the step contract, the naive
click-then-read gap (0 rows read right after the click), failure reports, timeouts and a
hanging action. Detection: the mapping of 16 Windows, macOS and Linux default-browser
identifiers, the Linux reads through `xdg-settings` and `xdg-mime`, and the Windows `reg` and
macOS LaunchServices *parsers* against sample output. Launch: detection, the loud fallback,
`PW_FALLBACK=0`, `AUTOMATION_BROWSER`, a pinned engine, and an installed Chrome that is
missing. After detection moved into Node, a smoke flow re-confirmed launch and a step.

**Not tested:** running `reg` on a real Windows machine and `plutil` on a real Mac, an
installed Chrome or Edge actually launching, Brave, Vivaldi or Opera by path, Playwright's
Firefox and WebKit builds, and headed mode. Treat those as likely to work and check them on
the first run.

## Troubleshooting

| Symptom | Check |
|---|---|
| `Chromium distribution 'chrome' is not found at ...` | The installed Chrome or Edge is missing: install it, or let the fallback use bundled Chromium |
| `Executable doesn't exist at ...` | That browser build is not installed: `npx playwright install <engine>`, or let the fallback use Chromium |
| `waitForResponse: Timeout ... exceeded`, though the call does happen | The `url` does not match: it is a substring or regex of the full URL, and `method` must match; the call may go to another origin |
| `network not quiet` | The app polls or streams. Set `quietMs: 0` for that step and confirm by element or response instead |
| Step passes but the next one reads stale data | A follow-up call started after the quiet window: add it to `responses` or confirm the new content with `text` |
| Right URL, wrong screen | Confirm with `text` or `visible` content, not only `navigates` |
| `the action did not complete within ...` | `act` is blocked (a click covered by an overlay, an `evaluate` that never returns); fix the cause rather than raising the timeout |
