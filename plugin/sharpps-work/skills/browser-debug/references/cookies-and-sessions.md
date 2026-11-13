# Cookies, sessions, and authentication

Summarized from the upstream `cookie-debugging` skill. Use for 401/403, redirects to
login, expiring sessions, `Cookie`/`Set-Cookie` problems, consent-banner conformance, and
SameSite or third-party-cookie warnings.

Cookie values are credentials. Report names, attributes, and counts; never print values,
and redact `Cookie`/`Set-Cookie` headers before quoting.

## What can see what

- `HttpOnly` cookies are invisible and immutable to page JavaScript, yet the browser
  attaches them to requests. Read them (names only) from the request `Cookie` header via
  `get_network_request`; see how they were configured in the `Set-Cookie` response header
  of the login response.
- Non-`HttpOnly` cookies: `evaluate_script` with
  `async () => await cookieStore.getAll()` (always `async`/`await`; it returns a Promise).
  `cookieStore` needs a secure context (https, localhost, 127.0.0.1); on plain http fall
  back to `() => document.cookie`.
- Changing cookies in JS (`cookieStore.set`/`delete`) works only for non-`HttpOnly`
  cookies. Deleting an `HttpOnly` cookie from JS **fails silently**. For a clean state
  open `new_page` with a unique `isolatedContext` instead.

## Pick the session

| Need | Use |
|---|---|
| Diagnose the user's live session or a live 401 | The existing page (`list_pages` for its `pageId`) |
| First visit, consent banner, zero-cookie guarantee, no residue | `new_page` with `isolatedContext: "<unique-name>"`, then `close_page` when done |

## Diagnose a 401/403 or login redirect

1. `list_network_requests` with `includePreservedRequests: true`; find the 401/403 or
   the 302/307.
2. `get_network_request` by `reqid`: was a `Cookie` header sent, and did it contain the
   expected token name?
3. No recent request listed: trigger one (`navigate_page` with `type: "reload"`, or
   `evaluate_script` `() => fetch(location.href)`), then inspect it.
4. Cookie missing or rejected: inspect the earlier login response's `Set-Cookie` for
   - **Path** mismatch (`Path=/api` but request is `/`),
   - **Domain** mismatch (`api.example.com` vs `sub.example.com`),
   - **`Secure`** on an `http://` page (never sent),
   - **`SameSite=Strict`** omitted on cross-site navigation,
   - **expiry** (`Expires`/`Max-Age` already passed).
5. `list_console_messages` with `types: ["issue"]` often states the browser's reason.

## Consent-banner conformance

1. `new_page` with `isolatedContext` (e.g. `consent-test-1`).
2. Baseline `cookieStore.getAll()` before touching the banner.
3. `list_network_requests` (any tracking beacons before consent?) and
   `list_console_messages` `types: ["issue"]`.
4. `take_snapshot`, `click` Decline/Reject All, re-run `cookieStore.getAll()`; only
   strictly necessary and consent-state cookies should remain.
5. Revocation: open the preferences control, deselect or revoke, re-query cookies, and
   check that later requests no longer fire trackers.
6. `close_page` to drop the context.

## SameSite, third-party cookies, CHIPS

- Fast: `list_console_messages` with `types: ["issue"]`, `includePreservedMessages: true`;
  look for `CookieIssue` entries (`SameSiteNoneInsecure`, `ThirdPartyCookiePhaseout`,
  `SchemefulSameSite`, `PartitionedCookies`).
- Deep: `lighthouse_audit` `mode: "navigation"`, then extract only the
  `third-party-cookies` audit from `report.json`:
  `node -e "const a=require('<report.json>').audits['third-party-cookies'];console.log(JSON.stringify({score:a?.score,displayValue:a?.displayValue,items:a?.details?.items}))"`

## Troubleshooting

- `cookieStore` undefined: insecure origin; use `document.cookie` or test over https.
- Empty or unresolved result: forgot `async`/`await`.
- Cookie not visible in JS: it is `HttpOnly`; read the request header instead.
- Delete did nothing: `HttpOnly`, or `Path`/`Domain` didn't match; use a fresh isolated
  context.
- Set but never sent: `Secure` on http, `Domain` too narrow, or browser rejection (check
  `issue` messages).
- Audits polluted by earlier cookies: always use a unique `isolatedContext`.
