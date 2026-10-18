# SSH transport, keys, and jump hosts

`shell_session_start`'s `mode` selects the transport. Call `shell_session_capabilities` to see
every mode currently registered on this server (today: `local_pty`, the default, and `ssh`) along
with each mode's supported auth methods and whether it requires a `host`.

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

For `mode="ssh"`: always pass an explicit `host` (and `username`/`port` when they're anything
other than SSH's own defaults). A session with implicit or guessed connection details is a session
the next caller can't fully trust: they can't tell from `shell_session_list` alone whether it's
connected where it's supposed to be.

## Authentication boundaries

Confirm the target and every jump host against authorized scope and the server allow-list.
Do not change `SHELL_MCP_SSH_ALLOWED_HOSTS` or other server policy to bypass a refusal.
Discover modes with `shell_session_capabilities`; do not assume that every server has
`ssh-legacy`. Use legacy transport only for an explicitly authorized host that needs it.

`identity_path` points to an existing key; never paste private-key material into terminal
writes or notes. The documented `passphrase` field is for encrypted-key authentication,
not a password-auth mode: use only the tool's designated credential mechanism under its
permission policy, never `shell_session_write`. If secure handling is unavailable, stop
and ask the owner to arrange agent/key access. Do not expose credentials in logs/context.

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

Before stopping a misbehaving shared session, check its state and context and resolve any
in-flight work with the user. Do not terminate another caller's work silently.
