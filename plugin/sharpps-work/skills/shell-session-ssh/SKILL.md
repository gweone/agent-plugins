---
name: shell-session-ssh
description: Open, reuse, resume, or stop a persistent SharpPS Shells SSH session, including existing private-key/agent authentication and multi-hop via jump hosts with ssh or ssh-legacy. Covers allowed targets, explicit connection details, state-before-input checks, and transport lifecycle; not local_pty session setup, password authentication, or ordinary one-shot commands.
---

# Persistent SSH shell sessions

SSH sessions use the same persistent, shared, ownerless `shell_session_*` tool family.
They survive calls and server restarts, leave connections running, and can be resumed by others.
For stateless work use the appropriate one-shot execution tool, not persistence by default.

## Connect only within approved scope

1. Require an explicit user request for persistence or confirmation before starting.
2. Call `shell_session_capabilities` for supported modes/auth; list existing sessions first.
3. Pass `mode="ssh"` and explicit `host`, plus `username`/`port` when not defaults (port 22).
4. The target must match `SHELL_MCP_SSH_ALLOWED_HOSTS`; unset means all SSH is refused.
   Confirm every target/hop is authorized; do not modify server policy to bypass refusals.
5. Use `auth_method="none"` for default identity/agent, or `"private_key"` with existing
   `identity_path`. `"password"` is unsupported; never type credentials into the terminal.
6. `via` is an ordered list of hop objects; each can use `ssh` or supported `ssh-legacy`.
   Top-level connection fields identify the final target, not the first jump host.

## Start once, inspect before input

Every start creates a new SSH connection and rebuilds all hops. For multiple commands,
start once without `command` for an interactive shell, then reuse that `session_id`.
Optional `command` is for exactly one remote check, not repeated reconnects.
Before writing to any session not just started by you, including an earlier conversation,
read list/get, screen/read **and** read_context; verify host/mode/command and in-flight state.
Read current output before later writes; do not answer unseen or stale prompts.
Stay in session write/read tools; use screen for full-screen TUIs, not every poll.
Session consent does not authorize arbitrary commands or sudo; preserve tool permission gates.
Never send secrets in terminal writes/context. For a sudo password prompt, stop and ask
for owner-arranged scoped `NOPASSWD`; use designated secure key-auth fields only.

## Resume, hand off, stop

One target/task, one authoritative live session. Inspect and resolve in-flight work before
stopping a failed session and replacing it; do not duplicate or silently kill another's work.
Record compact intent notes before blocking steps or on pivots; read the latest 2–3 on resume.
Stop sessions you started when done unless the user requested keeping them alive.
Stop preserves notes; clearing context is a separate deliberate action, never routine cleanup.

## Detailed references

- [SSH transport, authentication, and jump hosts](references/transport-and-authentication.md)
  — all connection fields, passphrase handling, legacy hops, allow-list, and tunnel reuse.
- [SSH lifecycle, context, and housekeeping](references/ssh-lifecycle-and-context.md)
  — independent consent/read-before-write rules, resume tools, sudo, notes, and stop behavior.

Examples document behavior only; do not connect or run remote commands automatically.
