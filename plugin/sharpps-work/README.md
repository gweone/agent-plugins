# sharpps-work

General office/documentation tooling for solutions built on the [SharpPS](https://github.com/gweone) framework — not tied to any one platform, unlike this marketplace's other plugins.

## Skills

| Skill | Covers |
|---|---|
| `generate-word` | Genuine OpenXML Word (`.docx`) documents via `python-docx` — headless, no Office/LibreOffice install needed. Covers title pages, styled headings, tables with a bold header row, embedding images with captions, note/callout paragraphs (no native element — built from a bold colored label), and verifying the output isn't corrupted before handing it over. |
| `codebase-memory-mcp` | Work with a [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) knowledge graph, an MCP server (not a slash command) with tree-sitter AST parsing, a lightweight semantic type-resolution layer, and cross-service HTTP/gRPC/GraphQL route matching that plain AST-only tools can't do. Two modes with one consent boundary. **Explore** (read-only): map architecture, trace callers/callees and routes across services, assess change impact; covers the 15 MCP tools, CLI mode on remote shells, language coverage tiers, working-tree freshness checks, and verifying confidence-scored cross-service claims. **Setup** (only when explicitly requested): the installer, which configures every detected client globally (MCP entries, agent profiles, skills, hooks), plus uninstall, indexing, environment variables, config, shared snapshots, and deletion, with permission denials treated as boundaries. References: graph analysis, freshness, installation and clients, indexing and configuration. |
| `shell-session` | Persistent, shared `shell_session_*` tmux sessions on a SharpPS Shells host — either a local pty or a remote shell over SSH — for interactive CLI wizards, remote logins, and long-running/resumable terminal work (e.g. a remote `claude` session) that a plain `shell_execute` one-shot can't handle. Covers the two transports (`mode="local_pty"` vs `mode="ssh"`, the latter needing an allow-listed `host` and never password auth — only `"none"`/agent or `"private_key"`), the four rules (explicit user confirmation before starting, always pass explicit connection details — `workspace` or `host` — on `shell_session_start`, stay inside the `shell_session_*` tool family for the life of a task, and check `shell_session_list`/`_get`/`_screen` before resuming or writing into a session you didn't start yourself), plus `shell_session_stop`, `shell_session_capabilities`, `shell_claude_sessions_list`, and how to run elevated (`sudo`) commands in a session without writing secrets into it. References: lifecycle and context (shared by both transports), local pty, SSH transport and authentication. |
| `structured-documentation` | A scannable "Findings / Feedback / Conclusion" markdown write-up on one workspace feature — what was found, built, or **converted from an existing doc** (a README, a research log, old notes) — saved to `docs/structured-documentation/` (namespaced so it doesn't mix into a project's other documentation). Covers a metadata header + summary + numbered per-finding subsections (so a reader can jump straight to what they need via a markdown outline), splitting a large multi-topic source document into one doc per topic instead of one oversized doc, keeping the three top-level sections doing distinct jobs (facts vs. judgment vs. decision), tracking unresolved work via a Status field and an Outstanding checklist, correlating multiple docs via a shared `README.md` (so a fresh session can pick up the folder's conventions and open work without the user re-explaining them), handling confidential content (never committing secrets/PII in cleartext to git history), and running the prose through the `humanizer` skill before saving, so it doesn't read like AI-generated text. |
| `browser-debug` | Troubleshoot a live page with [Chrome DevTools](https://github.com/ChromeDevTools/chrome-devtools-mcp) (`chrome-devtools-mcp`) through three access methods: local MCP (the default whenever it exists), a connector Chrome MCP, or the `chrome_cli.sh` CLI wrapper. The shared resolve-mcp reference decides which one a session uses, and other `browser-*` skills point to it. Symptom-to-tool playbook for console errors, failing/slow requests, CSS and layout, performance traces, Lighthouse, memory, and cookie/session bugs. Topic references folded in from the upstream Chrome DevTools skills: accessibility, LCP/performance, cookies and sessions, memory leaks, the DevTools UI and comment threads. Includes a CLI wrapper reference (`chrome_cli.sh` against the active profile, the full list of CLI commands, shared-browser rules) and a local-MCP setup reference (register the server, key flags, attach to a running Chrome, connection errors) and rules for untrusted page content and not leaking real logins. |
| `browser-automation` | Automate a web app in a fresh, isolated headless browser with Playwright (not the user's own Chrome), in two modes. **Test**: spec-first test matrix with written acceptance criteria, named `playwright-cli` sessions, assertions via `find`/`eval`/`console`/`requests`, PASS/FAIL/BLOCKED reports with evidence, and promoting verified flows into `npx playwright test` specs. **Capture**: real screenshots for documentation instead of mockups, login automation with `storageState` per role, local virtual-host routing (`--host-resolver-rules`, not Host-header interception), and selector pitfalls that cause silently-wrong captures. Shared setup covers install, bundled or installed Chrome, non-apt Linux hosts, smoke tests and cleanup. |
| `browser-recording` | [Jam](https://jam.dev) recording through the Jam Chrome extension, driven through Chrome access to the user's Chrome (connector MCP, attached local MCP, or CLI; resolved via browser-debug). Requires that access and the Jam extension installed and signed in. The agent starts the recording, the user picks the screen in Chrome's picker, the agent stops it, submits the form on the active tab, then finds, verifies and organizes the Jam via Jam MCP or the dashboard. Verified connected domains are required for console/network logs. Never claims a recording exists or logs were captured without proof. References: extension recording, setup, retrieval and analysis, open decisions. |

## Action skill workflow: Spec → Plan → Execution

The skills in this plugin run real commands (launch a browser, write a file, register an MCP
server) — never skip
straight to running one. **Spec** (resolve the concrete target — which screens, which document
structure — asking the user if ambiguous), **Plan** (state the exact steps about to run), then
**Execution/Build** (run them and verify the result, not just trust a zero exit code). See each
skill's own `SKILL.md` for how it applies this to that skill's specific commands.

## Pairing the two skills

The most common use of this plugin is together: `browser-automation` (capture mode) produces real screenshots of a
live app, `generate-word` assembles them into a guideline document with headings, captions, and
explanatory text around each one. Capture first, then build the document from the resulting
image files — don't interleave them, since a document build that fails partway through is much
cheaper to re-run than a capture session (which may depend on live, possibly-changing app state).

## Source

This plugin was built from real work producing a live-screenshot guideline document for a
Frappe/ERPNext-based project's branch-restriction feature — a headless-Chromium capture session
(including working around a local multi-tenant instance's Host-header routing) feeding into a
generated `.docx` with embedded figures. The techniques here are the app-agnostic parts of that
workflow, packaged for reuse in any project needing the same kind of documentation.
