# Local persistent session lifecycle and context

`shell_session_*` gives you a **persistent, shared, ownerless** terminal (backed by tmux) that
survives the tool-call boundary, survives the MCP server restarting, and can be picked up by any
caller — including you, in a completely different conversation, days later — as long as they know
the `session_id`. That's the whole point of it over `shell_execute`: `shell_execute` is a one-shot
command with no memory of itself; a shell session is a real, detached process that keeps running
past the call that started it until someone explicitly stops it.

That last point is why it's not a default tool — it leaves something running behind on the host.
The rules below are not optional style points — skipping any of them either starts a session
the user didn't ask for, or leaves the next caller (possibly you, later) guessing at what a
session is and where it stands.

## Rule 1 — Only start a session with explicit user confirmation

Call `shell_session_start` only when the user explicitly asks for it (a real-tty/pty need, a
remote SSH shell, `claude --remote-control`, or similar), or when you've confirmed with the user
first that this is what they want. Don't reach for it as a default or as a workaround for an
ordinary command — use `shell_execute` for one-off, stateless work instead. A shell session leaves
a real, detached process running past this call, backed by tmux, until someone calls
`shell_session_stop` — that's a real cost on the host that shouldn't be incurred without the user
knowing.

## Rule 2 — Always pass explicit connection details on start

For `mode="local_pty"`: always pass an explicit `workspace` — it silently falls back to the
server's home directory if omitted. Don't rely on that default; pass the actual working directory
the command needs (a repo checkout, a project root, etc.). Check `shell_workspace_info` first if
you're unsure what the default would even be, but the fix is always the same: pass `workspace`
explicitly, every time, no exceptions.

`command` is required for `mode="local_pty"`. Set `shell` only when overriding shell
auto-detection. Call `shell_session_capabilities` to discover current modes; this workflow
uses the local transport explicitly rather than relying on its being the default.

## Start once and reuse deliberately

Every `shell_session_start` creates a brand-new pty, never an attachment. For a multi-command
local task, start a persistent shell as the required `command` and then use writes to its
`session_id`. Never omit the required local command by copying the SSH interactive-shell pattern.
Before starting, inspect `shell_session_list` for an existing session covering this workspace/task.
Inspect status, pane, and context before reuse. One target/task, one authoritative live session:
if it is hung, garbled, in the wrong context, or otherwise unusable, resolve ownership/in-flight
work before an approved stop, then start a replacement. Do not silently kill another caller's work
or leave a bad session running while opening a second one.

## Rule 3 — Once you're in a session, stay in the shell_session_* tools

For the rest of a task that's running inside a session, keep using `shell_session_write` /
`shell_session_read` / `shell_session_screen` instead of switching to `shell_execute`,
`shell_read_file`, or `shell_write_file` for the same piece of work. The point of a session is
that it's one continuous process with its own state (a running wizard, a live `claude` session, a
remote SSH login, etc.) — splitting the same task across both tool families means part of it runs
outside that state, which is usually not what you want.

It's fine to use other tools for genuinely separate concerns (e.g. `shell_write_file` to stage an
input file the session will later read) — but if it's part of the same task you're driving through
the session, drive it through the session's own tools.

Use `shell_session_read` for line-oriented output (cheap, only what's new since your last call on
that `session_id`). Switch to `shell_session_screen` specifically for full-screen TUIs (a live
`claude` session, vim, htop, any ink/curses UI, including over SSH) where raw escape codes in
`shell_session_read`'s output are unreadable — `shell_session_screen` renders the resolved current
pane instead. Don't call it on every poll; it's the most expensive call in this tool family.

## Rule 4 — Resuming or attaching: check state before you type

Because sessions have no owner, **always** call `shell_session_list` (or `shell_session_get` for a
quick single-session status check) and then `shell_session_screen` (or `shell_session_read` for a
plain line-oriented shell) **and `shell_session_read_context`** before you write into a session
you didn't just start yourself — including resuming your own session from an earlier conversation.
`shell_session_list`'s `has_context` field flags at a glance which sessions have any notes worth
checking. A session's `command`, `mode`, `workspace`/`host`, `pid`, `alive`, and `age_seconds`
fields, plus whatever the pane currently shows and whatever context notes exist, are all you have
to go on, so read all of it before typing anything. Writing blind into a session you didn't just
create risks answering the wrong prompt, repeating a step that already happened, or stepping on
another caller's in-flight action.

## Context notes — when to write one, kept compact

`shell_session_write_context` logs a short freeform note against a `session_id`; it's entirely
optional and persists even after the session itself is stopped. It exists for exactly one
scenario: a task spans multiple steps or calls, and whoever picks the session back up next
(possibly you, possibly a different agent, possibly days later) needs to know intent that the pane
output alone won't show.

**Keep it to one compact line, not a running log** — e.g.
`"step 3/5 done (deps installed); next: run migration; if stuck, check /var/log/migrate.log"`.
Not a paragraph, not a copy of stdout. `shell_session_read_context` returns notes most-recent-first
with a `limit` (default 20) — because of that ordering, a resuming caller only ever needs the
latest one or two notes to know current state, so default reads to a small `limit` (e.g. 2–3)
rather than pulling the full history; only pull more if you're specifically investigating what
happened earlier. Writing one compact line per meaningful step, instead of one long note that gets
appended to, keeps both the write and the eventual read cheap.

Write a note when, and only when, one of these is true — this is a judgment call, not a checklist
to run every turn:

- **Right after starting** a session whose purpose won't be obvious from `command`/`workspace`
  alone (a multi-step task, a long-running job).
- **Right before a risky or blocking step** (sudo, a restart, a step likely to hang or fail) — so
  a useful note exists *before* getting stuck, not only in hindsight after.
- **On a genuine pivot** — task scope changed, a step failed and you're retrying differently, or
  you're about to stop responding for a while mid-task.

Skip it for routine steps that succeeded as expected, anything already obvious from recent pane
output, or a session you're about to `shell_session_stop` immediately after (final state was
reached, not stuck — nothing to hand off).

## Elevated commands and secrets

Session consent does not authorize every command or sudo operation. Check the specific command
against the user-approved task and preserve tool permission/approval gates; get further approval
where needed. For an authorized elevated command in an existing session:

1. Use `shell_session_write` with the command prefixed by `sudo`.
2. Read output with `shell_session_read` (or `shell_session_screen` for a TUI).
3. Never send a sudo password, API key, token, or other secret in `shell_session_write`
   or context notes. If sudo asks for a password, stop and ask the host owner to arrange
   appropriately scoped `NOPASSWD` access; do not configure it yourself automatically.

For an ordinary approved non-session task, use the appropriate execution tool
(`shell_execute(sudo=true)` where supported), not a forced persistent session.
SSH password auth (`auth_method="password"`) is unsupported: use `"none"` (default
identity/agent) or `"private_key"`; never type SSH credentials into a terminal.

## Housekeeping

- **`shell_session_list`** — see every tracked session (alive or recently exited), with its mode,
  command, workspace/host, pid, age, and `has_context`, before deciding whether to attach to an
  existing one or start a new one. Check this before starting a new session for a task that might
  already have one running.
- **`shell_session_get`** — a quick status snapshot of one session (same shape as
  `shell_session_read` but with no wait) for a fast "is this still alive / what mode is it" check.
- **`shell_session_write_context`** — log a short, compact note against a session_id (see the context-note guidance above for cadence). Persists after the session stops.
- **`shell_session_read_context`** — read those notes back, most-recent first; default to a small
  `limit` and check this before writing into any session you didn't just start.
- **`shell_session_clear_context`** — manually deletes all notes for a session_id. `shell_session_stop`
  never touches context on its own (context is meant to outlive a stopped session -- that's the whole
  point of it), so this is the one deliberate way to prune it. Call it when you judge a session's notes
  are genuinely stale or resolved -- e.g. picking up a workspace and finding old notes for a task that's
  long done -- not routinely, and not as part of a normal stop. Idempotent: clearing a session with no
  notes, or one that never existed, is a no-op, not an error.
- **`shell_session_stop`** — kills the session and frees its resources. Stop sessions you started
  once the task is genuinely done rather than leaving them running indefinitely. Does NOT clear its
  context notes -- use `shell_session_clear_context` separately if those are no longer needed either.
- **`shell_session_capabilities`** — lists every registered transport mode and its supported auth
  methods/requirements. Call this to discover valid `mode` values before starting a session.
- **`shell_claude_sessions_list`** — read-only listing of a project's `claude --resume` picker
  entries (title, age, branch, transcript size). Use this to find which Claude Code session to
  attach to via a session before you drive the picker yourself; it never selects or resumes
  anything on its own.

## Typical local lifecycle

1. Confirm persistence is requested, then list sessions and discover capabilities.
2. Inspect any reusable session before input; otherwise start explicitly:
   `shell_session_start(mode="local_pty", command, workspace="<explicit path>")`.
3. Drive the session with write/read or screen; record only useful compact context.
4. On later resume, inspect list/get, read_context (small limit), and screen/read before writing.
5. Call `shell_session_stop(session_id)` for sessions you started when genuinely finished,
   unless the user requested keeping them alive.
   Report the session_id and current state for an intentional handoff. Context persists after stop.
