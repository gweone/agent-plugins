---
name: replayr-testing
description: Write, run and review Playwright tests on SharpPS Replayr through its MCP server (list_projects, write_script, start_run, get_run_results, get_test_result, get_artifact_url, set_variable and more). Use when asked to test a site with Replayr, add or fix a Replayr script, start a run, explain why a run failed, store test credentials as secrets, or share a report.
---

# SharpPS Replayr over MCP

Replayr runs Playwright tests on its own runner and keeps a Jam-like report per test: steps, console, network, screenshots, video and trace. This skill is the working method for any agent that has the `sharpps-replayr` MCP server connected (endpoint `https://replayr.sharpps.dpdns.org/api/mcp`).

## Before anything

1. Call `list_workspaces`. If it fails with 401, the connector is not signed in: tell the user to authorize it (OAuth prompt, or an API token as `Authorization: Bearer rpt_...`). Do not ask them to paste a token into the chat.
2. A token or sign-in that covers several workspaces needs one chosen: set the `X-Replayr-Workspace` header, or add `?workspace=<organization id>` to the endpoint. Never guess.
3. Roles are enforced by the server: viewer reads, editor writes scripts and runs, admin manages projects, variables, profiles and sharing. A 403 means the role does not allow it; say so and stop.

## Working loop

1. `list_projects` (or `create_project` with the site's base URL, admin only).
2. Read the existing code with `list_scripts` and `read_script` before changing it.
3. Write with `write_script` (one file) or `upload_scripts` (many). Every save is a new version. Then `validate_scripts` and fix every reported problem before running.
4. `start_run` (scope project, file or one test title). Pass `environment_id` and `browser_profile_id` only when the user named them; otherwise the project defaults apply.
5. Poll `get_run` every 10 to 20 seconds until the status is passed, failed, timed_out or cancelled. Do not start the same run twice while one is active, and use `cancel_run` for a stuck one.
6. `get_run_results` for the list, `get_test_result` for one test (add `failed_requests_only: true` to see only 4xx/5xx), `get_test_history` for flakiness, `get_artifact_url` for a 15-minute video, trace or screenshot link.
7. Report plainly: what passed, what failed, the first error line, and the request or step that explains it. Do not claim a fix worked until a run passes.

## Script conventions

- Standard `@playwright/test` specs named `*.spec.ts`; use `baseURL`-relative paths (`page.goto("/login")`).
- Environment values come from `process.env.NAME`. Never write a password, token or personal email into a script.
- Wait for a state, not for time: prefer `expect(...).toBeVisible()`, `waitForResponse` and `waitForURL(..., { waitUntil: "commit" })` over fixed `waitForTimeout`.
- Several tests that share a login should not hammer a site that throttles; sign in once per file or use the project's login setup file.
- Trust only self-signed certificates for a named staging host (`ignoreHTTPSErrors` together with a host-specific setting), never globally.

## Secrets and data

- Store credentials with `set_variable` and `is_secret: true`, scoped to the project (and an environment when they differ). Secrets are write-only: they are masked in logs and never returned. Never echo a secret value in chat, a script, a commit or a share link description.
- A trace and the network log can contain cookies, tokens and typed passwords. Use dedicated test accounts, and leave trace out of share links unless the reader may see that data.
- Recordings are kept only for failed tests by default and are deleted from storage after the project's retention period (7 days by default); results and history stay.

## Guarded actions

- `delete_project`, `delete_run`, `delete_variable`, `delete_browser_profile`, `revoke_share_link` and `revoke_token` require `confirm: true`. Ask the user first, name the item, and only then pass it.
- `create_share_link` makes a public read-only URL that is shown once. Create one only when asked, and tell the user how to revoke it (`revoke_share_link`).
- Run tests only against sites the user owns or has permission to test. Do not run QA against production unless the user says so explicitly.

## Security checks on the site under test

Some sign-in forms are protected by reCAPTCHA or similar. Do not try to bypass, spoof or strip the check. Instead:

1. Make the script behave like a real user: let the page finish loading (so the challenge script can produce its token) before submitting.
2. Capture the login response status and the site's own message so a rejection is visible in the report.
3. If the site still rejects the login, report that the site's security check refused it and ask the site owner to allow the runner (IP allowlist or a staging-only switch).

## Reference

Tools: `list_workspaces`, `list_projects`, `create_project`, `update_project`, `delete_project`, `list_environments`, `create_environment`, `list_variables`, `set_variable`, `delete_variable`, `list_browser_profiles`, `upsert_browser_profile`, `delete_browser_profile`, `list_agents`, `get_endpoint_allowlist`, `set_endpoint_allowlist`, `list_scripts`, `read_script`, `write_script`, `validate_scripts`, `upload_scripts`, `list_script_versions`, `restore_script_version`, `start_run`, `list_runs`, `get_run`, `cancel_run`, `delete_run`, `get_run_results`, `get_test_result`, `get_test_history`, `get_artifact_url`, `create_share_link`, `list_share_links`, `revoke_share_link`, `list_tokens`, `revoke_token`, `get_audit_log`.
