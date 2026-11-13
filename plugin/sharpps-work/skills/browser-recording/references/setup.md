# Setup: prerequisites and capability detection

All prerequisites below are required except Jam MCP. If a required item is missing, stop and tell the user what to install, sign in to, or connect. Do not fall back to a Recording Link or any other recording method.

## Prerequisites

| Requirement | Owner | How the agent checks |
|---|---|---|
| Chrome MCP (for example SharpPS Chrome) connected to the user's real Chrome | User / administrator | `list_pages`, `trigger_extension_action`, `click`, `type_text`, `wait_for` and `evaluate_script` (service worker) are exposed in this session and `list_pages` succeeds. |
| Jam Chrome extension installed in that Chrome | User | `list_pages` lists `chrome-extension://iohjgamcilhbgmhbnllfolmkmmekfmci/sw.js`, and `trigger_extension_action` offers that id. |
| User signed in to the right Jam workspace in that extension | User | In the Jam service worker, `chrome.storage.local` has `$jam-memoized-store` with a `user`, and `jam-global-minimal-shared-store-4` has `auth.hasAccessToJamSite: true`. |
| Jam MCP (optional) | Administrator | `searchJams`, `getDetails`, `listFolders`, `updateJam` are exposed. Without them, the user manages the Jam in the dashboard. |
| Target domain connected and verified in Jam (optional) | User / administrator | Needed only for console/network logs; see [Jam's custom recording domain guide](https://jam.dev/docs/custom-recording-domain). |

A skill being installed does not prove any tool is connected. Detect tools at runtime; do not infer them from documentation or prior sessions.

## Capability use

| Operation | Tool | Without it |
|---|---|---|
| Start, interact, stop, submit | Chrome MCP | Required: stop and ask the user to connect it. |
| Find the submitted Jam | `searchJams` | User finds it in the Jam dashboard and shares its URL. |
| Verify what was captured | `getDetails`, then `getUserEvents` / `getFrames` as needed | User confirms in the dashboard; label it user-reported, not agent-verified. |
| Move to a folder | `listFolders`, `updateJam` | User moves it in the dashboard. |
| Diagnostics | `getConsoleLogs`, `getNetworkRequests`, `getEvents` | Say which diagnostics were not accessible. |

## Responsibilities

| Step | Owner |
|---|---|
| Install the Jam extension and sign in | User |
| Connect Chrome MCP to that Chrome | User / administrator |
| Start the recording, interact, stop, submit the form | Agent, through Chrome MCP |
| Choose the tab or screen in Chrome's native picker | User |
| Find, verify, organize the Jam | Agent through Jam MCP, or user in the dashboard |

## Failures

| Symptom | Likely cause | Action |
|---|---|---|
| Chrome MCP tools missing or `list_pages` fails | Not connected, or the browser connection dropped | Stop; ask the user to connect or reconnect Chrome MCP. Do not claim anything started. |
| No Jam service worker in `list_pages` | Extension not installed or disabled | Ask the user to install or enable Jam. |
| No Jam user in storage | Signed out | Ask the user to sign in through the Jam extension. |
| `trigger_extension_action`: "Could not find an active browser window" | Chrome window not focused | Retry once; then ask the user to focus Chrome. |
| Jam MCP auth or permission error | Wrong team or role | Report it; continue verification in the dashboard with the user. |
