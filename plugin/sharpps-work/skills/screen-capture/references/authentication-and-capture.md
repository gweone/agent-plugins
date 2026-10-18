# Authentication, selectors, and capture debugging

## Login and session reuse

Only use approved accounts, credential sources, roles, and UI actions. Login, submitting forms,
creating records, dismissing prompts, or changing data must remain within the agreed capture
scope; stop for confirmation before an unapproved write, destructive action, or external effect.
Use a fresh isolated browser context; persistent profiles and saved state contain sensitive
session data and must not be shared, committed, or reused outside the approved scope.

Create the context explicitly before the login example:

```js
const context = await browser.newContext();
const page = await context.newPage();
```

```js
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
await page.fill('#login_email', username);      // selector names vary by app - inspect first
await page.fill('#login_password', password);
await page.click('.btn-login');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000);   // illustrative fallback, not proof rendering is complete
// Prefer an app-specific visible heading/ready state before the final screenshot.

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
- Only retrieve credentials from an explicitly approved source. When a credential must be pulled from a remote/containerized environment (e.g. an env var
  inside a Docker container), redirect it straight to a file rather than displaying it, so the
  value never appears in the command's own stdout capture, only in the file the script then
  reads:
  - bash/macOS/Linux: `docker exec container sh -c 'printf "%s" "$SECRET_VAR"' > .secret_file`
  - PowerShell/Windows: `docker exec container sh -c 'printf "%s" "$SECRET_VAR"' | Out-File -Encoding utf8 -NoNewline .secret_file`
    (`-NoNewline` controls newlines, not encoding. Explicit `-Encoding utf8` selects UTF-8;
    Windows PowerShell 5.1 writes a UTF-8 BOM, whereas PowerShell 7 writes UTF-8 without one.
    Use a BOM-aware reader or PowerShell 7 `-Encoding utf8NoBOM` when exact bytes matter.
    `Set-Content` also needs an explicit encoding; it is not a byte-preserving substitute.)
- Restrict temporary credential/state files to the current user; keep them out of git, logs,
  screenshots, and deliverables. Do not print their contents while debugging.
- Delete any file holding a real credential (and any `storageState.json` containing session
  cookies) once capture is done — these are session artifacts, not deliverables.

## Selector robustness — pitfalls that cause silently-wrong captures

- **Never use a bare `page.click('text=...')` for common words** ("Create", "Save", "Edit") on
  a page with a sidebar/nav — it can match an unrelated element elsewhere on the page and
  navigate somewhere completely different, and the script won't error, it'll just screenshot the
  wrong page. Scope the selector to the actual toolbar/container:
  `page.locator('.page-actions button:has-text("Create")')`.
- **When a locator resolves to multiple elements**, strict locator actions such as
  `locator.click()` may throw; non-strict legacy selector actions or explicit `.first()` can
  target an unintended match. Dropdown menus commonly render hidden duplicates. Prefer a
  selector that resolves to exactly one intended, visible element; use `.first()`/`.last()`
  only as a last resort with an explicit visibility check.
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

## Privacy and cleanup

Review every final image for credentials, tokens, PII, and unrelated confidential content.
Prefer approved test data; redact or recapture before sharing and do not retain unsafe originals
in deliverables. Close browser contexts and delete task-created temporary credentials, role
state files, sensitive persistent profiles, and intermediate/debug captures when no longer
needed. Do not delete a user's pre-existing profile or credential store. Keep only approved
final screenshots in the agreed output location.
