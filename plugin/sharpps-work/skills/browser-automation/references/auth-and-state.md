# Auth, roles and saved state

Only use approved accounts, credential sources, roles and UI actions. Login, submitting
forms, creating records, dismissing prompts or changing data must stay within the agreed
scope; stop for confirmation before an unapproved write, destructive action or external
effect. Use a fresh isolated browser context. Persistent profiles and saved state contain
sensitive session data and must not be shared, committed or reused outside the approved
scope.

## Roles

If several roles matter (for example an admin view and a restricted end-user view), log in
once per role and keep a separate saved state per role. A restricted view needs its own
account; do not reuse the admin state for it.

## CLI: sessions and saved state

- Log in once per role in its own session; reuse it with `state-save role_admin.json` and
  `state-load role_admin.json`.
- Treat those files as secrets: keep them out of git and delete them when finished.

## Scripts: login and `storageState`

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

Reuse the saved session in later scripts instead of logging in again:

```js
const context = await browser.newContext({ storageState: 'auth_state.json' });
```

Save a separate `storageState` file per role.

## Credentials

- Never echo a password or secret into any command's visible output or into a script
  printed to the transcript.
- Only retrieve credentials from an explicitly approved source. When a credential must be
  pulled from a remote or containerized environment (for example an env var inside a Docker
  container), redirect it straight to a file rather than displaying it, so the value never
  appears in the command's own stdout capture, only in the file the script then reads:
  - bash/macOS/Linux: `docker exec container sh -c 'printf "%s" "$SECRET_VAR"' > .secret_file`
  - PowerShell/Windows: `docker exec container sh -c 'printf "%s" "$SECRET_VAR"' | Out-File -Encoding utf8 -NoNewline .secret_file`
    (`-NoNewline` controls newlines, not encoding. Explicit `-Encoding utf8` selects UTF-8;
    Windows PowerShell 5.1 writes a UTF-8 BOM, whereas PowerShell 7 writes UTF-8 without one.
    Use a BOM-aware reader or PowerShell 7 `-Encoding utf8NoBOM` when exact bytes matter.
    `Set-Content` also needs an explicit encoding; it is not a byte-preserving substitute.)
- Restrict temporary credential and state files to the current user; keep them out of git,
  logs, screenshots and deliverables. Do not print their contents while debugging.
- Delete any file holding a real credential, and any saved state containing session
  cookies, once the work is done. These are session artifacts, not deliverables. Do not
  delete a user's pre-existing profile or credential store.
