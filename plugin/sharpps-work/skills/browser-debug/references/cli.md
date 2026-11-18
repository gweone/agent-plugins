# Chrome DevTools via the CLI wrapper

The CLI method is the wrapper `chrome_cli.sh` on the SharpPS cloud host. It runs the
upstream `chrome-devtools` command against the same Chrome the connector drives: the
**active profile** chosen on the `/chrome/` dashboard. Use it when no MCP tools are
available, or for a scripted or batch run that writes results to files (see
[resolve-mcp](resolve-mcp.md) for when to pick it).

Always call the wrapper, never `chrome-devtools` directly: the wrapper resolves the
profile, the browser endpoint and the daemon for you. In the examples below `chrome_cli.sh`
stands for `/opt/github/trading-mcp/scripts/chrome_cli.sh`.

## Check it is available

```bash
test -x /opt/github/trading-mcp/scripts/chrome_cli.sh && chrome_cli.sh --info
```

`--info` prints the active profile, a masked endpoint and the daemon state. If the wrapper
does not exist (not the SharpPS host), the CLI method is unavailable: say so and offer the
other methods. Do not improvise by installing or starting the raw CLI yourself.

## What the wrapper does

- Every call reads the active profile, resolves the browser endpoint (an SSH read through
  `chrome_remote.sh --print`), and starts or restarts the background daemon only when the
  profile or the browser ID changed, or the daemon is down. Then it runs your command.
- State (selected page, snapshots, console history) lives in the daemon, so it persists
  between calls while the daemon stays up.
- Switching the profile on the dashboard is picked up by the next call. No service restart.
- It always targets the active profile's Chrome: the user's real browser with their
  logins. It cannot give you an isolated or throwaway browser; use the local MCP for that.
- The daemon runs with the extensions and network-mock categories on, matching the
  connector. Other optional tool groups (PWA, WebAuthn, `click_at`, WebMCP) are off.

## Wrapper options

```bash
chrome_cli.sh --info                 # active profile, masked endpoint, daemon state
chrome_cli.sh --sync                 # force a restart on the current endpoint
CHROME_CLI_NO_SYNC=1 chrome_cli.sh <tool> ...   # skip the profile check (no SSH call)
```

Use `CHROME_CLI_NO_SYNC=1` for a rapid burst of commands once the first call has synced.
Run `--sync` after the CLI package is upgraded; a normal call does not notice a version
change.

## Command shape

```bash
chrome_cli.sh <tool> [positional args] [--flags]
chrome_cli.sh <tool> --help          # exact arguments for a tool
```

- Required arguments are positional; page-scoped tools take the `pageId` first. Optional
  arguments are flags. Exception: `evaluate_script` takes the function first and
  `--pageId` as a flag.
- Output is Markdown-like text. Add `--output-format=json` for JSON.
- Tool names match the MCP tools, so the [debugging playbook](debugging-playbook.md)
  applies as written; only the call syntax changes.

## Core loop

```bash
chrome_cli.sh list_pages                         # find the pageId
chrome_cli.sh take_snapshot 1                    # text snapshot with element uids
chrome_cli.sh click 1 "1_4"                      # act on a uid from the snapshot
chrome_cli.sh fill 1 "1_7" "text"
chrome_cli.sh take_snapshot 1                    # re-snapshot after any change
```

The browser is the user's real Chrome, so `list_pages` shows all their tabs. Pick the tab
that matches the target URL, ask if it is ambiguous, and open a new tab with
`new_page "<url>"` rather than navigating one they are using. Snapshot `uid`s go stale
after the page changes; re-snapshot before the next action.

## Command cheat sheet

| Goal | Command |
|---|---|
| Navigate | `navigate_page 1 --url "https://example.com"`, `--type reload --ignoreCache true`, `--type back` |
| New / select / close tab | `new_page "<url>"`, `select_page 1 --bringToFront true`, `close_page 1` |
| Console | `list_console_messages 1 --types error`, `get_console_message 1 <msgid>` |
| Network | `list_network_requests 1 --resourceTypes fetch`, `get_network_request 1 --reqid 5 --responseFilePath res.md` |
| Run JS | `evaluate_script "() => document.title" --pageId 1`; a file: `evaluate_script --pageId 1 --sourcePath ./s.js --format script` |
| Screenshot | `take_screenshot 1 --filePath s.png` (`--fullPage true`, `--uid <uid>`) |
| CSS | `get_css_styles 1 "1_4" --pageSize 20` |
| Emulate | `emulate 1 --colorScheme dark --viewport 1920x1080` (each call replaces earlier settings) |
| Performance | `performance_start_trace 1 --reload true --autoStop true --filePath t.json.gz`, `performance_analyze_insight 1 <insightSetId> <insight>` |
| Lighthouse | `lighthouse_audit 1 --mode navigation --outputDirPath ./out` |
| Memory | `take_heapsnapshot 1 ./snap.heapsnapshot`, then `get_heapsnapshot_*` / `compare_heapsnapshots` ([memory-leaks](memory-leaks.md)) |
| Extensions | `list_extensions`, `trigger_extension_action <id>` |

Quote JavaScript so the shell does not expand it (single quotes are safest around `$` and
backticks). For anything longer than one line, write it to a file and use `--sourcePath`
with `--format script`. Send large results to `--filePath` and read the file selectively.

## Web Store extensions

`trigger_extension_action` only finds unpacked extensions; for a Web Store extension it
reports "not found". The connector falls back to the extension's service worker; do the
same by hand. Get the worker id (`sw-N`) from `list_pages`, match its
`chrome-extension://<id>/` to the extension, then:

```bash
chrome_cli.sh evaluate_script \
  "async () => { await chrome.action.openPopup(); return true; }" --serviceWorkerId sw-1
```

## Shared browser and secrets

- The connector and the wrapper drive the same browser. Do not drive one page through both
  at once, and re-run `list_pages` after switching between them: page IDs are per
  connection.
- The browser endpoint is a bearer-like secret. `--info` masks it. Never run
  `chrome-devtools status` directly: it prints the full endpoint in the daemon arguments.
- The CLI can read and write files anywhere on the host (`--filePath`, `--outputDirPath`,
  `upload_file`). Write to a task directory, and keep traces, heap snapshots and screenshots
  out of shared output when they could hold personal data.

## Troubleshooting

| Symptom | Check |
|---|---|
| `chrome-devtools not found` | The CLI package is missing on the host. Ask the user to install it once (`npm i -g chrome-devtools-mcp@latest`), then retry |
| `could not resolve the active profile / endpoint` | No active profile on the `/chrome/` dashboard, the SSH tunnel to the workstation is down, or Chrome has remote debugging off. Use "Test connection" on `/chrome/`, then retry |
| Commands hang | Chrome on the workstation may be waiting for someone to allow the remote debugging connection; ask the user to approve it |
| Wrong pages or wrong browser | `chrome_cli.sh --info` to see the active profile, then `--sync` |
| Tool "unknown command" | Its tool group is off in the wrapper (only extensions and network mocks are on) |
| Version mismatch warning | `chrome_cli.sh --sync` restarts the daemon on the installed version |

## Finish

Close tabs you opened. Leave the daemon running (it is cheap and shared), and never stop or
restart the user's Chrome.
