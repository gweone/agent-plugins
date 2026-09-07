# sharpps-work

General office/documentation tooling for solutions built on the [SharpPS](https://github.com/gweone) framework — not tied to any one platform, unlike this marketplace's other plugins.

## Skills

| Skill | Covers |
|---|---|
| `screen-capture` | Real screenshots of a running web app via a headless Chromium (Playwright), for documentation that shows the actual UI rather than mockups. Covers environment setup on non-apt Linux hosts, reaching a local multi-tenant/reverse-proxied instance whose real domain doesn't resolve to the dev environment (`--host-resolver-rules`, not Host-header route interception — documented as unreliable), login automation with session reuse via `storageState`, selector-robustness pitfalls that cause silently-wrong captures (ambiguous text selectors, `.last()` in a changing grid), and iterative screenshot-driven debugging. |
| `generate-word` | Genuine OpenXML Word (`.docx`) documents via `python-docx` — headless, no Office/LibreOffice install needed. Covers title pages, styled headings, tables with a bold header row, embedding images with captions, note/callout paragraphs (no native element — built from a bold colored label), and verifying the output isn't corrupted before handing it over. |
| `codebase-memory-mcp` | Turn a codebase in any language into a queryable knowledge graph via [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp), an MCP server (not a slash command) — tree-sitter AST + a lightweight semantic type-resolution layer, plus cross-service HTTP/gRPC/GraphQL route matching that plain AST-only tools can't do. Covers the two-step install (binary fetch + separate `codebase-memory-mcp install` agent-registration step, which changes tool-call behavior across every detected client on the machine), the 15 MCP tools, CLI equivalents, language coverage tiers, and verifying confidence-scored cross-service claims before trusting them. |
| `structured-documentation` | A scannable "Findings / Feedback / Conclusion" markdown write-up on one workspace feature — what was found, built, or **converted from an existing doc** (a README, a research log, old notes) — saved to `docs/structured-documentation/` (namespaced so it doesn't mix into a project's other documentation). Covers a metadata header + summary + numbered per-finding subsections (so a reader can jump straight to what they need via a markdown outline), splitting a large multi-topic source document into one doc per topic instead of one oversized doc, keeping the three top-level sections doing distinct jobs (facts vs. judgment vs. decision), tracking unresolved work via a Status field and an Outstanding checklist, correlating multiple docs via a shared `README.md` (so a fresh session can pick up the folder's conventions and open work without the user re-explaining them), handling confidential content (never committing secrets/PII in cleartext to git history), and running the prose through the `humanizer` skill before saving, so it doesn't read like AI-generated text. |

## Action skill workflow: Spec → Plan → Execution

The skills in this plugin run real commands (launch a browser, write a file, register an MCP
server) — never skip
straight to running one. **Spec** (resolve the concrete target — which screens, which document
structure — asking the user if ambiguous), **Plan** (state the exact steps about to run), then
**Execution/Build** (run them and verify the result, not just trust a zero exit code). See each
skill's own `SKILL.md` for how it applies this to that skill's specific commands.

## Pairing the two skills

The most common use of this plugin is together: `screen-capture` produces real screenshots of a
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
