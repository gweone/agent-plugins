---
name: shell-session
description: Use when the user explicitly asks for a persistent, shared terminal session on a SharpPS Shells host — for example, an interactive CLI wizard, a remote claude session (claude --resume, --remote-control), a remote shell over SSH, or terminal work the user wants to keep alive and resumable. Covers the requirement to confirm with the user before starting a session, always passing an explicit workspace (for local_pty) or host (for ssh) on shell_session_start, staying inside the shell_session_* tool family for the life of a task, and checking shell_session_list/_screen/_get before resuming or writing into a session you did not start yourself. Trigger for "pty session", "shell session", "tmux session", "ssh session", "resume that session", "remote-control claude", or any request to keep a terminal task alive across calls.
---

# Shell session workflow (SharpPS Shells)

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

## Two transports, one tool family

`shell_session_start`'s `mode` selects the transport. Call `shell_session_capabilities` to see
every mode currently registered on this server (today: `local_pty`, the default, and `ssh`) along
with each mode's supported auth methods and whether it requires a `host`.

- **`mode="local_pty"`** (default) — a real pty on this host. `command` is required. `workspace`
  sets the working directory and `shell` overrides shell auto-detection.
- **`mode="ssh"`** — a remote shell over SSH. `host` is required and must match this server's
  `SHELL_MCP_SSH_ALLOWED_HOSTS` allow-list (every session is refused if that's unset — SSH is
  disabled by default). Optional: `command` (runs as the remote command instead of an interactive
  login shell), `port` (default 22), `username`, `auth_method` (`"none"` for the default
  identity/agent, or `"private_key"` with `identity_path` pointing at an existing key file —
  **never `"password"`**; there is no password-auth option here), `passphrase` for an
  encrypted key.
- **`via`** — reaches a target behind one or more jump hosts in a single `shell_session_start`
  call, instead of manually chaining separate SSH sessions. Pass a list of hop objects (each with
  its own `mode`, `host`, `port`, `username`, `auth_method`, `identity_path`); the hops connect in
  order and the final `host`/`port`/etc. on the top-level call is the actual target reached
  through that tunnel. Each hop can independently be `"ssh"` or `"ssh-legacy"` (for an
  older/legacy jump host that only offers SHA-1-era host keys), so a modern target behind a
  legacy jump box — or vice versa — is one call, not two nested sessions to manage separately.

Whichever transport you use, the rest of the workflow (Rules 1–4 below, plus housekeeping) is
identical — everything reads/writes through the same `shell_session_*` tools regardless of
`mode`.

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

For `mode="ssh"`: always pass an explicit `host` (and `username`/`port` when they're anything
other than SSH's own defaults). A session with implicit or guessed connection details is a session
the next caller can't fully trust: they can't tell from `shell_session_list` alone whether it's
connected where it's supposed to be.

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

## Every `shell_session_start` call opens a brand-new session — reuse deliberately

`shell_session_start` never attaches to anything existing — it always builds a fresh pty (or,
for `mode="ssh"`, a fresh SSH connection, and with `via` a full multi-hop tunnel chain rebuilt
from scratch) on every single call. That cost is invisible for a single check but adds up fast
across a multi-step task, especially over a slow or multi-hop connection.

- The one-shot `command` argument on `shell_session_start` is for exactly one check. If you
  already know there will be a second command against the same target, don't call
  `shell_session_start` with `command` repeatedly — start once **without** `command` (which
  drops into an interactive shell) and drive the rest of the work through
  `shell_session_write`/`shell_session_read` (or `shell_session_screen` for TUIs) on that one
  `session_id`.
- **One target, one live session.** Before starting a session, check `shell_session_list` for
  one already open to the same target and reuse it instead of opening another. If an existing
  session is misbehaving (hung, wrong shell state, garbled prompt, stuck in the wrong
  directory/context), `shell_session_stop` it first and only then start its replacement — never
  leave a bad session running and open a second one "to be safe"; that leaves two live sessions
  to the same target with no way to tell which one is authoritative.

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

## Elevated commands (sudo)

For this skill, elevated execution does **not** require a separate user confirmation step once
the session itself has already been started with user confirmation per Rule 1. When the user
explicitly requested a session (local or SSH) and a command needs elevated privileges, execute it
through `sudo` with `shell_session_write`. Otherwise, use the appropriate non-session execution
tool (`shell_execute(sudo=true)`). Do not force a persistent session for ordinary tasks.

Example workflow:

1. Use `shell_session_write` with the command prefixed by `sudo`.
2. Read the output with `shell_session_read` (or `shell_session_screen` for a TUI) and continue
   through the same session.
3. Never put a sudo password, API key, token, or other secret into `shell_session_write`. If sudo
   asks for a password, stop and ask the host owner to configure appropriate scoped `NOPASSWD`
   access instead. Likewise, never attempt password-based SSH auth — `auth_method="password"` is
   not supported; use `"none"` (default identity/agent) or `"private_key"` instead.

## Housekeeping

- **`shell_session_list`** — see every tracked session (alive or recently exited), with its mode,
  command, workspace/host, pid, age, and `has_context`, before deciding whether to attach to an
  existing one or start a new one. Check this before starting a new session for a task that might
  already have one running.
- **`shell_session_get`** — a quick status snapshot of one session (same shape as
  `shell_session_read` but with no wait) for a fast "is this still alive / what mode is it" check.
- **`shell_session_write_context`** — log a short, compact note against a session_id (see
  "Context notes" above for cadence). Persists after the session stops.
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

## Typical lifecycle

1. Confirm with the user (or confirm they explicitly asked) that a persistent session is actually
   what's needed — not just a one-off command.
2. `shell_session_list` — check nothing already covers this task.
3. `shell_session_start(mode="local_pty", command, workspace="<explicit path>")` or
   `shell_session_start(mode="ssh", host="<explicit host>", ...)`.
4. Drive the task with `shell_session_write` / `shell_session_read` (or `shell_session_screen` for
   TUIs), writing a short context note at start, before risky steps, or on a pivot (see "Context
   notes" above — not on every step).
5. If picking this session back up later or in a different conversation: `shell_session_list`,
   `shell_session_read_context` (small `limit`), and `shell_session_screen`/`shell_session_read`
   **before** the first `shell_session_write`.
6. `shell_session_stop(session_id)` once the task is genuinely done.
