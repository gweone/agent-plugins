# Test execution

Commands are from `@playwright/cli`; run `playwright-cli --help` for your version.
Examples assume `-s=qa` (a named session), shown once per block for brevity.

## Run a scenario

```bash
playwright-cli -s=qa open https://app.example.test
playwright-cli -s=qa snapshot --depth=4        # element refs (e12, e15, ...)
playwright-cli -s=qa fill e12 "test-user" 
playwright-cli -s=qa click e15
playwright-cli -s=qa find "Welcome"            # assert expected text is present
playwright-cli -s=qa screenshot --filename=evidence/login_pass.png
```

- Refs come from the latest snapshot. After navigation or a DOM change, snapshot again.
- `fill <ref> <text> --submit` fills and presses Enter. `select`, `check`, `uncheck`,
  `upload`, `hover`, `press` cover the rest.
- Shorten large pages with `snapshot <ref>` (one element) or `--depth=N`.

## Assertions

The CLI has no assert command; decide pass/fail yourself from observable facts:

| Check | How |
|---|---|
| Text/element present | `find "text"` or `find --regex "/pattern/i"` returns a match; no match means fail |
| Current URL/title | the page header printed after each command, or `eval "location.pathname"` |
| Value/state | `eval "el => el.value" <ref>`, `eval "document.title"` |
| No JS errors | `console error` should list nothing unexpected |
| Backend call made and succeeded | `requests`, then `request <index>` for status and body |
| Negative case | trigger the invalid input and confirm the error message *and* no side effect |

Write the expected value down before looking at the actual one.

## Auth and roles

- Log in once per role in its own session; reuse with `state-save role_admin.json` /
  `state-load role_admin.json`. Treat those files as secrets: keep them out of git and
  delete them when finished.
- Test permission boundaries with a low-privilege role as well as an admin, and
  confirm the restricted role *cannot* reach the restricted screen.

## Controlled conditions

- Mock or fail a dependency with `route <pattern>`; clear with `unroute`.
- Viewports and devices: `resize <w> <h>`, `open --device="iPhone 15"`, `--mobile`.
- Appearance: `set-color-scheme dark`, `set-reduced-motion`, etc.
- Dialogs: `dialog-accept` / `dialog-dismiss`.

## Evidence for failures

On FAIL, capture before changing anything: screenshot, `console`, the relevant
`request <index>`, and the snapshot filename. For a hard-to-see failure use
`tracing-start` / `tracing-stop` or `video-start` / `video-stop`. Then hand the repro
to [browser-debug](../../browser-debug/SKILL.md) if the cause isn't obvious.

## Report template

```markdown
| # | Scenario | Role | Expected | Actual | Result | Evidence |
|---|---|---|---|---|---|---|
| 1 | Valid login | user | Dashboard shown | Dashboard shown | PASS | evidence/login_pass.png |
| 2 | Wrong password | user | Error, stay on login | Stack trace shown | FAIL | evidence/login_fail.png, console |
| 3 | Export | admin | CSV downloads | not run: no test data | BLOCKED | n/a |
```

Close with counts (pass/fail/blocked), the environment and build tested, and what was
not covered.

## Promote to a regression suite

After a flow is verified by hand, turn it into a spec instead of re-running it ad hoc.

- `recording-start` ... `recording-stop` prints the performed actions as Playwright
  code, and `generate-locator <ref>` gives a stable locator. Prefer role/label/test-id
  locators over positional ones, and review before committing, since recorded code
  often needs tighter assertions.
- Put the criteria in as `expect(...)` assertions; a spec with no expects tests nothing.
- Run: `PLAYWRIGHT_HTML_OPEN=never npx playwright test`.
- Debug a failing spec: `PLAYWRIGHT_HTML_OPEN=never npx playwright test --debug=cli`
  (run in the background; it pauses and prints a session name), then
  `playwright-cli attach <session>`. Stop the background run when done.
- Rerun to confirm green before reporting a fix.
