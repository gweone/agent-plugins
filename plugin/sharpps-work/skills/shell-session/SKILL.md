---
name: shell-session
description: Start, drive, resume, hand off, or stop a persistent shared SharpPS Shells terminal (shell_session_* tools, tmux-backed), either a local pty (mode local_pty) or an SSH session (mode ssh/ssh-legacy, private-key or agent auth, multi-hop via jump hosts). Use for local interactive CLI wizards, tmux/pty tasks, claude --resume or --remote-control, remote shells, and terminal work kept alive across calls. Requires explicit session consent, an explicit workspace or host, allowed targets, state-before-input checks, and lifecycle cleanup; not password authentication or ordinary one-shot commands.
---

# Persistent shell sessions (local pty and SSH)

A `shell_session_*` terminal is persistent, shared, ownerless, and tmux-backed. It survives
calls and server restarts until stopped; knowing `session_id` permits resumption, and it can
be resumed by other callers. For one-off stateless work, use the one-shot execution tool
(`shell_execute`), not a persistent session by default.

## Pick the transport

| Transport | `mode` | Use for | Required on start | Reference |
|---|---|---|---|---|
| Local pty | `local_pty` | Interactive CLI wizards, tmux/pty tasks, `claude --resume` / `--remote-control` on this host | `command` and an explicit `workspace` | [local pty](references/local-pty.md) |
| SSH | `ssh` (hops may use `ssh-legacy`) | A remote shell, including targets behind jump hosts | An explicit authorized `host`; `username`/`port` when not default | [SSH transport and authentication](references/ssh-transport-and-authentication.md) |

## Start deliberately

1. Start only if the user explicitly requested persistence or confirmed it first.
2. Call `shell_session_capabilities` for supported modes/auth; select the `mode` explicitly
   rather than relying on the default.
3. Check `shell_session_list` for an existing session covering the target/task.
4. Pass the transport's required connection details every time (table above). Omitting
   `workspace` silently selects the server home; use `shell_workspace_info` if uncertain.
5. Every `shell_session_start` creates a new pty or SSH connection (rebuilding all `via` hops);
   it never attaches to an existing one. For multiple commands, start once and drive that
   `session_id`: locally pass a shell as the required `command`; over SSH start without
   `command` for an interactive shell. SSH `command` is for exactly one remote check.
6. SSH only: the target and every hop must match `SHELL_MCP_SSH_ALLOWED_HOSTS` (unset refuses
   all SSH). Do not modify server policy to bypass a refusal. Use `auth_method="none"`
   (default identity/agent) or `"private_key"` with an existing `identity_path`;
   `"password"` is unsupported and credentials never go into the terminal. Top-level connection
   fields identify the final target, not the first jump host.

## Inspect before input

- Before writing to any session not just started by you, including one from an earlier
  conversation, read `shell_session_list`/`shell_session_get`, then screen/read **and**
  read_context. Check command, mode, workspace/host, pid, alive, age_seconds, has_context,
  pane, and notes.
- Read current output before subsequent writes; do not answer an unseen or stale prompt.
- Stay in `shell_session_write`/`shell_session_read` for this task's process state. Use
  `shell_session_screen` for full-screen TUIs (`claude`, vim, htop), not every line-output poll.
- Session consent is not blanket command/sudo approval; preserve all tool permission gates.
- Never send passwords, private keys, API tokens, or other secrets in terminal writes or notes.
  If sudo prompts for a password, stop and ask the owner for scoped `NOPASSWD` arrangements;
  use designated secure key-auth fields only for SSH credentials.

## Resume, hand off, stop

Keep one authoritative session per target/task. Inspect and resolve in-flight work before
stopping a bad session and replacing it; do not leave duplicates or kill another caller's work.
Use compact `shell_session_write_context` notes for non-obvious intent, blocking steps, or
pivots. Read the latest 2–3 notes with `shell_session_read_context` on resume; notes are not a
stdout log. Stop sessions you started when genuinely done unless the user requested keeping
them alive. `shell_session_stop` preserves notes; `shell_session_clear_context` is a deliberate,
separate action, never routine cleanup.

## Detailed guidance

- [Lifecycle, context, tools, and elevated commands](references/lifecycle-and-context.md):
  shared rules for both transports: consent, reuse, read-before-write, note cadence, sudo and
  secrets, housekeeping tools, resume picker.
- [Local pty](references/local-pty.md): explicit workspace, required command, shell override,
  multi-command reuse, local lifecycle.
- [SSH transport, authentication, and jump hosts](references/ssh-transport-and-authentication.md):
  all connection fields, passphrase handling, legacy hops, allow-list, tunnel reuse, SSH lifecycle.

Examples document behavior only; this skill does not authorize starting sessions, running
commands, or connecting to remote hosts automatically.
