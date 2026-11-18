# Agent-driven extension recording (Chrome MCP + Jam extension)

Verified end to end on 2026-11-13 (Jam 5.101.1) and again 2026-11-15 (Jam 5.102.0): tab-capture with the submit form on the recorded tab and on another tab; a failed-login flow (three throwaway submits); and a Window-mode multi-tab recording that captured events + network from two tabs. Findings on the length cap, picker modes, network metadata-vs-bodies, and the "Share this tab instead" ribbon are in the sections below.

Use this when Chrome access to the user's real Chrome is available: a Chrome MCP, a local MCP attached with `--autoConnect`, or the CLI. Resolve which one per [resolve-mcp](../../browser-debug/references/resolve-mcp.md). The tool names below are the same on all three; with the CLI they are `chrome_cli.sh` commands (for example `evaluate_script ... --serviceWorkerId sw-N`, `select_page <id> --bringToFront true`). The agent drives every step except the native screen picker.

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

## Picker mode: Tab vs Window vs Entire screen

The picker chooses the **video surface only**; it does not by itself decide what network/console is captured. Network and events come from Jam instrumenting the tabs it **tracks** (`capture.payload.trackedTabs`), a set separate from the video.

| Mode | Video | Tracked tabs / network + events |
|---|---|---|
| **Chrome Tab** | One tab; does not follow tab switches | The tracked tab(s). Best when the whole flow is in that one tab. |
| **Window** | The whole Chrome window; tab switches are visible | Jam **adds each tab you visit/interact with to `trackedTabs`**, so events + network span all visited tabs — but only after you `bringToFront` that tab. Best for multi-tab flows. Verified 2026-11-15: `trackedTabs` grew from `[example.com]` to `[example.com, wikipedia.org]` once the second tab was fronted, and the Jam held events + network from both. |
| **Entire screen** | Everything on screen, other apps too | Same tracked-tab rule; Jam still cannot read network from non-Chrome apps or untracked tabs. |

You **cannot switch the captured tab mid-recording from CDP**. Focusing a non-captured tab shows Chrome's native ribbon ("Sharing… · Stop sharing · **Share this tab instead**"); that ribbon is browser chrome, not page DOM — invisible to `take_snapshot`/`take_screenshot` and unclickable by CDP (same wall as the picker). So if a flow spans tabs, pick **Window** before starting; do not plan to switch the captured surface later.

## What network and console actually capture

- **Network/event metadata** — request URL, method, status, content-type, timing, plus user events (clicks, typing, navigations) — is captured for **any tracked tab, regardless of whether the domain is connected/verified**. Verified 2026-11-15: a Window recording captured 52 requests from unconnected `iana.org` (×11) and `en.wikipedia.org`/wikimedia (×41).
- **Request/response bodies and full console** need a **verified connected domain**. In that same Jam every captured request had an empty body (`contentSizeBucket: empty`), and console was 0.
- So report "request bodies / console unavailable" for unverified domains, never "no network".

## Recording length limit

Free Jam caps recording length (~5 min observed). At the cap Jam **auto-stops on its own and drops into the draft/submit form** — nothing is lost, but a single continuous take cannot exceed the cap. For a long scenario: split into sub-cap takes (one session/attempt each), upgrade Jam, or use an uncapped recorder (Playwright video). A recording that ends with no `End recording` click and lands in `draft` has usually hit the cap, not failed.

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
   - Ask the user to pick in the native picker and click Share: **Chrome Tab -> <target tab title>** for a single-tab flow, or **Window** (the Chrome window) when the flow spans multiple tabs. Name the exact tab title; warn about look-alike tabs on the same site.
   - Do not wait for the user to reply. Poll Jam's `capture.state.name` every ~15 seconds, up to 3 checks (about 45 seconds total). A cloud shell `sleep 15` between reads is a reliable timer.
   - As soon as a check shows `recording`, confirm the target page snapshot shows `End recording` and a running timer, say recording started, and continue to step 5 automatically.
   - If all 3 checks still show `pre_recording`, stop and ask the user to pick the screen (the picker was not answered). Do not re-arm or re-trigger; the armed `pre_recording` session is still waiting. Resume the poll when they reply.
   - If state is `idle` (not `pre_recording`) when polling starts, arming was lost: re-arm from step 3.
5. **Interact**
   - Perform the actions the task asks for on the target page: clicks, navigations, and form entry. Keep them clearly identifiable (accordions, a public link and back) when the task is just a capture demo.
   - Never type the user's real credentials or secrets. Submitting a form with obviously fake throwaway values (for example to capture a failed-login flow) is allowed when the user asks; the values must not be real. Jam masks `password` inputs (events show `is_anonymized: true`), but still never enter a real secret.
   - **Single recorded tab (Tab mode):** the recorded tab is the captured surface, so CDP clicks land and are recorded even while it sits in the background; you need not bring it to front, and it is fine to leave it backgrounded if the user is working elsewhere.
   - **Multiple tabs (Window / Entire screen):** `select_page(pageId, bringToFront: true)` on each tab **before** acting on it. The window/screen video only shows the foreground tab, and Jam adds a tab to `trackedTabs` (and so captures its events + network) when you bring it forward and interact. A background interaction on a second, not-yet-fronted tab can be missed from both the video and the tracked set. Switching back to an earlier tab is just another `bringToFront` (verified 2026-11-15, including an isolated-context tab).
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
| Recording ended with no `End recording` click, state `draft` | Hit the free-plan length cap (~5 min) | Not a failure: submit or discard the draft; split long scenarios into shorter takes. |
| Need to switch the captured tab mid-recording | Not possible via CDP ("Share this tab instead" is native UI) | Re-plan with **Window** mode; do not attempt to click the ribbon. |
