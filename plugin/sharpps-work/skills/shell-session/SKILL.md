---
name: shell-session
description: Start, drive, resume, hand off, or stop a local persistent shared terminal on a SharpPS Shells host using local_pty. Use for local interactive CLI wizards, tmux/pty tasks, claude --resume or --remote-control, and terminal work kept alive across calls. Requires explicit session consent, workspace, state-before-input checks, and lifecycle cleanup; not SSH/key/jump-host transport or ordinary one-shot commands.
---

# Local persistent shell sessions

A `shell_session_*` terminal is persistent, shared, ownerless, and tmux-backed.
It survives calls and server restarts until stopped; knowing `session_id` permits resumption.
For one-off stateless work, use `shell_execute`, not a persistent session by default.

## Start deliberately

1. Start only if the user explicitly requested persistence or confirmed it first.
2. Call `shell_session_capabilities`; select `mode="local_pty"` explicitly.
3. Check `shell_session_list` for an existing session covering the workspace/task.
4. For a new session, pass required `command` and an explicit `workspace` every time.
   Omission silently selects the server home; use `shell_workspace_info` if uncertain.
5. For multiple commands, use a shell as the required local `command` and drive it once.
   Every `shell_session_start` creates a new pty; it never attaches to an existing one.

## Inspect before input

- Before writing to any session not just started by you—including an earlier conversation—
  inspect `shell_session_list`/`shell_session_get`, then screen/read **and** read_context.
- Check command, mode, workspace, pid, alive, age_seconds, has_context, pane, and notes.
- Read current output before subsequent writes; do not answer an unseen or stale prompt.
- Stay in `shell_session_write`/`shell_session_read` for this task's process state.
  Use `shell_session_screen` for TUIs (`claude`, vim, htop), not every line-output poll.
- Session consent is not blanket command/sudo approval; preserve all tool permission gates.
- Never send passwords, private keys, API tokens, or other secrets in terminal writes or notes.
  If sudo prompts for a password, stop and ask the owner for scoped `NOPASSWD` arrangements.

## Resume, hand off, stop

Keep one authoritative session per target/task. Inspect and resolve in-flight work before
stopping a bad session and replacing it; do not leave duplicates or kill another caller's work.
Use compact `shell_session_write_context` notes for non-obvious intent, blocking steps, or pivots.
Read the latest 2–3 notes with `shell_session_read_context` on resume; notes are not a stdout log.
Stop sessions you started when genuinely done unless the user requested keeping them alive.
`shell_session_stop` preserves notes; `shell_session_clear_context` is deliberate, not routine.

## Detailed reference

- [Local lifecycle, context, tools, and elevated commands](references/local-lifecycle-and-context.md)
  — full read-before-write flow, note cadence, resume picker, safe reuse, and housekeeping.

Examples document behavior only; this skill does not authorize starting or running commands.
