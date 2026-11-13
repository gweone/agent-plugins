# Agent-driven extension recording (Chrome MCP + Jam extension)

Verified end to end on 2026-11-13 (Jam extension 5.101.1, Chrome 157 on Windows, chrome-devtools-mcp 1.13) with two Jams that captured the intended tab, one with the submit form on the recorded tab and one with it on another tab.

Use this when a Chrome MCP (for example SharpPS Chrome) is attached to the user's real Chrome. The agent drives every step except the native screen picker.

Run the whole flow end to end in one pass: start, wait for the picker, interact, stop, submit, verify. Do not pause at the draft to ask whether to submit; submit and verify by default. Stop to ask the user only (a) at the screen picker, and (b) when a required prerequisite, the picker, or verification fails. If the user said beforehand to leave it as a draft, stop after step 7 instead.

## Prerequisites

- **Jam extension installed** in that Chrome: `list_pages` lists `chrome-extension://iohjgamcilhbgmhbnllfolmkmmekfmci/sw.js`.
- **User signed in** to the extension: in that service worker, `chrome.storage.local` has `$jam-memoized-store` with a `user`, and `jam-global-minimal-shared-store-4` has `auth.hasAccessToJamSite: true`.
- If either is missing, stop and ask the user to install or sign in. Do not continue.

## Who does what

| Step | Owner | Why |
|---|---|---|
| Open the Jam popup, choose Record Desktop | Agent | `trigger_extension_action` + popup `click` work through CDP. |
| Choose what to share in the native picker | **User** | The OS/Chrome picker is outside the page; CDP cannot reach it. The agent polls for `recording` rather than blocking on a reply. |
| Interact with the target page | Agent | Normal `click` / `navigate_page` on the target page, even in a background tab. |
| End recording | Agent | Jam injects an `End recording` button into the recorded page. |
| Find and fill the submit form, click Create | Agent | The form is a Jam iframe; locate its tab first (step 7). |
| Verify the Jam | Agent | Jam MCP `searchJams` + `getDetails`. |

Never claim the recording started until the Phase 2 poll shows state `recording`.

## Why the picker cannot be automated here

- Jam's tab-only mode (`toggle-video`, Ctrl+Shift+Space, `chrome.tabCapture`) needs the `activeTab` grant. Chrome grants it only for a real user gesture on the extension (toolbar click or real keyboard shortcut). CDP clicks, CDP key presses and a CDP-opened popup do not count: `tabCapture.getMediaStreamId` fails with "Extension has not been invoked for the current page".
- So the popup offers only **Record Desktop**, which uses the native picker.
- Chrome switches such as `--auto-select-desktop-capture-source` or `--auto-select-tab-capture-source-by-title` can auto-answer the picker, but require relaunching Chrome with them. Do not do this unless the user asks for it.
- Do not inject OS keystrokes or edit Jam's files to bypass the picker.

## Flow

### Phase 1: start the recording via Chrome MCP

1. **Preflight**
   - `list_pages`; note the target page id and every other open tab. Do not touch tabs the user is working in (for example a logged-in admin tab).
   - Read Jam state from its service worker (`evaluate_script` with the Jam `serviceWorkerId`, read-only): `chrome.storage.local` key `jam-global-minimal-shared-store-4` holds `capture.state.name` (`idle`, `pre_recording`, `recording`, `draft`) and `draftMetadataMap`. Proceed only from `idle` with no unfinished draft; otherwise report and preserve the draft.
2. **Target tab**
   - Open or reuse the target page; verify the final URL (redirects included) with `take_snapshot`.
   - `select_page` with `bringToFront: true` so it is the active tab when recording is armed.
3. **Arm the recording**
   - `trigger_extension_action` for Jam. If it returns "Could not find an active browser window", retry once (Chrome window was not focused).
   - Snapshot the popup page (`chrome-extension://<jam-id>/popup.html`) and click **Record Desktop**. The popup then closes; a later "session closed" error from that popup is expected.
   - Confirm state `pre_recording` with `atTabId`/`atUrl` = target. The recorded page shows Jam's toolbar with "Select a screen to share".
### Phase 2: user picks the screen

4. **Hand off the picker, then poll (do not block on a reply)**
   - Ask the user to pick **Chrome Tab -> <target tab title>** (or Entire screen with the target visible) and click Share. Name the exact tab title; warn about look-alike tabs on the same site.
   - Do not wait for the user to reply. Poll Jam's `capture.state.name` every ~15 seconds, up to 3 checks (about 45 seconds total). A cloud shell `sleep 15` between reads is a reliable timer.
   - As soon as a check shows `recording`, confirm the target page snapshot shows `End recording` and a running timer, say recording started, and continue to step 5 automatically.
   - If all 3 checks still show `pre_recording`, stop and ask the user to pick the screen (the picker was not answered). Do not re-arm or re-trigger; the armed `pre_recording` session is still waiting. Resume the poll when they reply.
   - If state is `idle` (not `pre_recording`) when polling starts, arming was lost: re-arm from step 3.
5. **Interact**
   - Perform the actions the task asks for on the target page: clicks, navigations, and form entry. Keep them clearly identifiable (accordions, a public link and back) when the task is just a capture demo.
   - Never type the user's real credentials or secrets. Submitting a form with obviously fake throwaway values (for example to capture a failed-login flow) is allowed when the user asks; the values must not be real. Jam masks `password` inputs (events show `is_anonymized: true`), but still never enter a real secret.
   - Keep the target in the background if the user is working elsewhere; CDP clicks still land and are recorded.
### Phase 3: stop via Chrome MCP and submit the form on the active tab

6. **Stop**
   - Navigation re-injects the toolbar: `wait_for` text `End recording` on the target page, then click it. Jam shows "Gathering console logs...".
7. **Locate the submit form**: it opens on the user's **active tab**, which may not be the recorded tab.
   - In the Jam service worker: `chrome.runtime.getContexts({})`, keep the context whose `documentUrl` contains `iui.html`, base64-decode its `t` query param; it contains `["tabId",<id>]`. `chrome.tabs.get(id)` gives that tab's URL and title; match it to a `list_pages` page.
   - Jam state is now `draft` with `atUrl` still the recorded page.
   - If the host tab is large (for example a chat app), save the snapshot to a file (`take_snapshot` with `filePath`) and extract the section under `RootWebArea "Jam UI"`.
8. **Submit**
   - Click the `Title` heading inside the Jam UI, `type_text` the title with `submitKey: Enter`, then `type_text` the description. No secrets or personal data.
   - Click **Create**. The "Creating a link for you, on its way shortly!" toast may not be detectable by `wait_for` when the form is on another tab; do not rely on it.
### Phase 4: manage the Jam via Jam MCP or the dashboard

9. **Verify (mandatory)**
   - Jam state returns to `idle` with an empty `draftMetadataMap`.
   - `searchJams` with `window.from` just before the recording, newest first; match by title and creation time.
   - `getDetails`: `type` video, `duration` > 0, `url` = target page, and timeline events (clicks, navigations) that are on the target site. A matching title alone is not proof.
   - Move it with `updateJam` when the user names a folder (`listFolders` first; use the folder id).
   - Without Jam MCP: ask the user to open the Jam in the dashboard, confirm it shows the target page, move it if wanted, and share its URL. Label anything not inspected by the agent as user-reported.

## Failure signals

| Signal | Meaning | Action |
|---|---|---|
| Popup offers only Desktop | Expected without a real user gesture | Use the Desktop flow above. |
| State stays `pre_recording` | Picker still open | Wait for the user; do not re-trigger. |
| `getDetails.url` or timeline shows another site | Wrong picker choice or wrong active tab when armed | Report FAIL; do not reuse the Jam as proof. |
| No `iui.html` context after stop (before submit) | Form not shown yet | Re-check after a few seconds; then scan `list_pages` snapshots for `Create`. Never discard the draft. |
| No `iui.html` context after Create | Expected: the form closes on submit, leaving only `BACKGROUND` | Not an error. Confirm success by state `idle` with empty `draftMetadataMap` and the new Jam in `searchJams`. |
| Picker still unanswered after 3 polls | User has not shared a screen | Stop and ask the user to pick; keep the `pre_recording` session, do not re-arm. |
