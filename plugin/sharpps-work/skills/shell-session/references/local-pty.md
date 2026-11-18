# Local `local_pty` sessions

Transport-specific rules for `mode="local_pty"`. Shared consent, read-before-write, context-note,
and housekeeping rules are in [lifecycle and context](lifecycle-and-context.md).

## Start call

`shell_session_start(mode="local_pty", command, workspace="<explicit path>")`

- **`workspace`** — always pass the actual working directory the command needs (a repo
  checkout, a project root, etc.), every time, no exceptions. It silently falls back to the
  server's home directory if omitted. Check `shell_workspace_info` first if you're unsure what
  the default would even be.
- **`command`** — required for `local_pty`. Never omit it by copying the SSH interactive-shell
  pattern.
- **`shell`** — set only to override shell auto-detection.
- **`mode`** — call `shell_session_capabilities` to discover current modes and pass
  `mode="local_pty"` explicitly rather than relying on its being the default.

## Start once and reuse deliberately

Every `shell_session_start` creates a brand-new pty, never an attachment. For a multi-command
local task, start a persistent shell as the required `command` and then use writes to its
`session_id`. Before starting, inspect `shell_session_list` for an existing session covering this
workspace/task, and inspect its status, pane, and context before reuse. One target/task, one
authoritative live session; see the shared reuse rules.

Typical local uses: a running wizard, a live `claude` session (`claude --resume`,
`claude --remote-control`), vim/htop-style TUIs (use `shell_session_screen`, not raw reads).
For finding which Claude Code session to resume, use `shell_claude_sessions_list` first.

## Typical local lifecycle

1. Confirm persistence is requested, then list sessions and discover capabilities.
2. Inspect any reusable session before input; otherwise start explicitly:
   `shell_session_start(mode="local_pty", command, workspace="<explicit path>")`.
3. Drive the session with write/read or screen; record only useful compact context.
4. On later resume, inspect list/get, read_context (small limit), and screen/read before writing.
5. Call `shell_session_stop(session_id)` for sessions you started when genuinely finished,
   unless the user requested keeping them alive.
   Report the session_id and current state for an intentional handoff. Context persists after stop.
