---
name: pty-sessions
description: Use whenever a task needs a persistent, shared PTY/tmux session on a SharpPS Shells host instead of a one-off shell_execute call — driving an interactive CLI wizard, a remote claude session (claude --resume, --remote-control), or any long-running terminal work that a different conversation or agent might resume later. Covers the required workspace on shell_pty_start, planning before acting via shell_pty_plan_context, staying inside the pty_* tool family for the life of a task so the context log stays a complete audit trail, and populating context (shell_pty_context, shell_pty_screen) before resuming or writing into a session you did not start yourself. Trigger for "pty session", "tmux session", "resume that session", "remote-control claude", or any request to keep a terminal task alive across calls.
---

# PTY session workflow (SharpPS Shells)

`shell_pty_*` gives you a **persistent, shared, ownerless** terminal (backed by tmux) that
survives the tool-call boundary, survives the MCP server restarting, and can be picked up by any
caller — including you, in a completely different conversation, days later — as long as they know
the `session_id`. That's the whole point of it over `shell_execute`: `shell_execute` is a one-shot
command with no memory of itself; a pty session is a durable, resumable place where several
callers' worth of history has to make sense to whoever reads it next.

Four rules fall out of that, and they are not optional style points — skipping any of them breaks
the audit trail the next caller (possibly you, later) depends on to safely resume the session.

## Rule 1 — Always pass an explicit `workspace` on start

`shell_pty_start(command, context, workspace, shell, capture_seconds)` will silently fall back to
the server's home directory if `workspace` is omitted. Don't rely on that default — always pass
the actual working directory the command needs (a repo checkout, a project root, etc.), the same
way you would pick `workspace` for `shell_execute`. A session with an implicit workspace is a
session the next caller can't fully trust: they can't tell from `shell_pty_list` alone whether the
command is running where it's supposed to, and re-deriving it means re-reading the whole context
log instead of just glancing at one field.

Check `shell_workspace_info` first if you're unsure what the default would even be, but the fix is
always the same: pass `workspace` explicitly, every time, no exceptions.

## Rule 2 — Plan before you act, and log the plan to context

Before doing anything meaningful in a session — starting it, sending a risky keystroke, answering
an interactive prompt, stopping it — write the plan to the session's context log first with
`shell_pty_plan_context(session_id, context)`. This costs nothing (no keystrokes sent, no wait) and
means the log reads as "here's what I was about to do" → "here's what happened," not just a stream
of raw output with no stated intent behind it.

`shell_pty_start`'s own `context` argument is this same idea at creation time: write it as a short
plan ("about to run the interactive migration wizard against staging"), not a bare label ("migration").
`shell_pty_write`'s `context` argument works the same way for every subsequent keystroke — it's
required, and it's the caller's one chance to tell a future reader *why*, not just *what*.

Keep every context string short and compact, like a commit message — a log line, not a report.

## Rule 3 — Once you're in a pty session, stay in the pty_* tools

For the rest of a task that's running inside a pty session, keep using `shell_pty_write` /
`shell_pty_read` / `shell_pty_screen` (and `shell_pty_plan_context` for pure logging) instead of
switching to `shell_execute`, `shell_read_file`, or `shell_write_file` for the same piece of work.
This matters because **the context log is the only record that survives across callers and
conversations** — splitting one task across both tool families splits that record too, so the next
caller sees a session with gaps: things happened that never got logged there.

It's fine to use other tools for genuinely separate concerns (e.g. `shell_write_file` to stage an
input file the session will later read) — but if it's part of the same task you're driving through
the session, drive it through the session's own tools, and log the aside via
`shell_pty_plan_context` if it isn't obvious from the pty output alone.

Use `shell_pty_read` for line-oriented output (cheap, only what's new since your last call). Switch
to `shell_pty_screen` specifically for full-screen TUIs (a live `claude` session, vim, htop, any
ink/curses UI) where raw escape codes in `shell_pty_read`'s output are unreadable — `shell_pty_screen`
renders the resolved current pane instead. Don't call it on every poll; it's the most expensive call
in this tool family.

## Rule 4 — Resuming or attaching: populate context first

Because sessions have no owner, **always** call `shell_pty_context(session_id, limit)` before you
write into a session you didn't just start yourself — including resuming your own session from an
earlier conversation. Read enough history to understand what the session is for and what state
it's likely in, and if it's a full-screen TUI, also call `shell_pty_screen` to see the actual
current pane before typing anything. Writing blind into a session you didn't just create risks
answering the wrong prompt, repeating a step that already happened, or stepping on another caller's
in-flight action.

`shell_pty_context` works even after a session has been stopped — the log outlives the tmux session
itself, which is what `shell_pty_stop` actually tears down. So "populate context first" applies
whether the session is alive or not; a stopped session's log still tells you what it was for and
how it ended.

## Housekeeping

- **`shell_pty_list`** — see every tracked session (alive or recently exited), with its command,
  workspace, latest context, and age, before deciding whether to attach to an existing one or start
  a new one. Check this before starting a new session for a task that might already have one running.
- **`shell_pty_compact_context`** — once a session's log has grown long, read the fuller history
  first (`shell_pty_context` with a high `limit`), write your own compact summary of what it covers,
  then call this to fold everything older than `keep_recent` entries into that one summary entry.
  Do this rather than letting a long-running session's log grow unbounded.
- **`shell_pty_stop`** — pass a `context` explaining why you're stopping it; that gets logged before
  teardown so a later reader sees it was deliberate, not a crash.
- **`shell_claude_sessions_list`** — read-only listing of a project's `claude --resume` picker
  entries (title, age, branch, transcript size). Use this to find which Claude Code session to
  attach to via a pty before you drive the picker yourself; it never selects or resumes anything on
  its own.

## Typical lifecycle

1. `shell_pty_list` — check nothing already covers this task.
2. `shell_pty_start(command, context="<plan for this session>", workspace="<explicit path>")`.
3. Before each meaningful action: `shell_pty_plan_context(session_id, context="<what I'm about to do>")`.
4. Drive the task with `shell_pty_write` / `shell_pty_read` (or `shell_pty_screen` for TUIs) only —
   no `shell_execute` for the same task.
5. If picking this session back up later or in a different conversation: `shell_pty_context` (and
   `shell_pty_screen` if it's a TUI) **before** the first `shell_pty_write`.
6. `shell_pty_compact_context` if the log has grown long.
7. `shell_pty_stop(session_id, context="<why>")` once the task is genuinely done.
