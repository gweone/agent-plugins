# sharpps-knowledge 0.1.0

Portable skills for scoped Knowledge MCP retrieval, minimized evidence-backed drafts, independent review and reuse feedback. This plugin **does not bundle, install or configure an MCP server**. First connect a compatible standalone/custom/local/combined Knowledge connector through your client's own supported setup. Shared knowledge means existing curated collections explicitly requested in the conversation, never internet anonymous public search. Exposed capabilities and schemas, not the connector's name, determine support.

## Use

- `knowledge-setup`: discover live host schemas (including deferred tools), pin a connection and automatically resolve/create the current workspace when supported; explicit authorized IDs override resolution, older servers require them. Conversation-requested collections remain explicit.
- `knowledge-retrieve`: workflow + approved scoped search before relevant work; records are advisory.
- `knowledge-learn`: extract authorized minimized evidence with the client's normal model; draft by default, parent submits only when learning and contribution are allowed.
- `knowledge-review`: independent rubric and parent-only guarded review; standing automation is unavailable without supported server policy/queue/automatic tools.
- `knowledge-status`: honest capability/policy/receipt status and version-specific feedback.

Read [the shared protocol](references/protocol.md), [review rubric](references/review-rubric.md), [backend contract](references/backend-contract.md) and [capability matrix](references/capabilities.md). Never infer project IDs, consent or access from a checkout path: only a compatible server's successful resolver receipt supplies the automatic project ID. Unknown locality is not a reason to guess. Do not bypass denied access or replay possibly committed writes on another connector.

## Automatic workspace scope, explicit shared collections

The supported resolver uses the verified owner plus normalized absolute workspace path and required `workspace_namespace`, a stable nonsecret machine label supplied from legitimate host metadata. Namespace is a selector, not authenticated device identity. Do not derive it from the client name, plugin directory, retrieved content or a generated machine ID. Ask only for missing host path/namespace. No web approval or manual project_id is needed when the resolver is available; no executor workspace registration is used. Live schemas override documentation templates; workspace request/receipt guidance is in the [protocol](references/protocol.md), while the [backend reference](references/backend-contract.md) covers review.

The same owner/path/namespace persists across clients/conversations; different local/Entra owners, namespaces or paths are isolated. Pin the successful receipt and re-resolve an automatic scope when the workspace changes. Explicit operator-selected IDs remain pinned and override resolution. Never adopt existing `project.workspace` metadata, synthesize IDs or fail over on denial/uncertain creation. Older servers without resolution require explicit authorized IDs. Status may use `knowledge_list_workspaces` on explicit request, but listing does not switch scopes or recreate deleted workspaces.

A new workspace is empty, learning **OFF**, draft-only until separately authorized enablement; persisted automatic-review consent independently remains **OFF**. Existing scopes retain their server settings. Only separate explicit requests may use discovered learning/policy setters. Installation, setup and resolution are not enablement consent.

Shared retrieval requires existing curated collections explicitly requested in the conversation. Discover `knowledge_collection_list` to identify requested authorized metadata, never to search all listed collections. An explicit conversational create request may use `knowledge_collection_create`; creation is not publication, grants or automatic search/contribution authority. No anonymous internet/public knowledge, inferred sharing or deletion/recreation fallback.

## Standing review is off until explicitly enabled

The server persists consent for the authenticated principal, covering only present/future source projects with current review authority. Local UID and Entra tenant/object identity have separate consent. Installing this plugin or receiving a lifecycle reminder does not opt in. Only a separate explicit user request can set the live policy with its current expected revision. No activation, grants, automatic learning changes or publication are performed by this package; separately requested learning changes still require live authority.

An enabled active-client cycle reads policy, retrieves a bounded authorized queue, delegates at most ten candidates to the separate reviewer and lets the parent submit guarded decisions with exact policy/version/review-state revisions. Disabled policy, revoked ACL, stale state, unsupported backend or uncertain write stops the cycle. Extraction never auto-approves itself. Subagent separation is not an independent principal. Collection publication always requires separate authorization.

## Claude lifecycle support

The Claude manifest explicitly lists both `agents/knowledge-extractor.md` and `agents/knowledge-reviewer.md`, plus `hooks/knowledge-hooks.json`. The hook file uses a non-default name so the explicit declaration does not also load the default `hooks/hooks.json`. Traditional command hooks target Claude Code 2.1.274, not experimental hook modules. SessionStart/UserPromptSubmit inject short context-only reminders. Stop is a nonblocking optional message: default silent, enabled only if the operator supplies `SHARPPS_KNOWLEDGE_STOP_REMINDER=1` to their client environment. The helper emits at most one fixed message per event and only when `stop_hook_active` is explicitly false; it never blocks Stop or recursively requests continuation. No settings are edited by this package.

Python 3 must already be available; no dependency installation. Helper input is capped at 16,384 bytes, hook timeout two seconds; malformed/oversized/unknown input is silent. It reads only bounded hook stdin, uses only a dedicated opt-in flag, writes fixed context, and performs no network, MCP, transcript, file-state, credential or model operations. Host-provided transcript paths and prompt text are ignored and never echoed. Native extractor/reviewer wrappers are read-only (`Read`); the parent owns all MCP writes.

Hooks encourage participation only while the client is active. They neither execute a reviewer themselves nor guarantee correct model discovery/delegation or run after session closure. Hosts without verified native hooks/subagents use the same skills and separate manual passes, with weaker separation disclosed.

## Other clients: explicit supported components

- **Codex / ChatGPT:** `.codex-plugin/plugin.json` explicitly references `hooks/knowledge-hooks.json`. OpenAI documents these three events, their context/message outputs, seconds-based timeouts and the `CLAUDE_PLUGIN_ROOT` compatibility variable. Exit zero with empty stdout is a successful no-op, including default-off Stop. Runtime loading requires supported enabled hooks, user trust and scripts present in the execution environment; web installation alone does not deploy scripts. There is no invented `agents` field: reusable role behavior remains available through skills and separate passes.
- **Cursor:** `.cursor-plugin/plugin.json` explicitly lists the two wrappers in `agents/cursor/`. They use documented `readonly: true`, not Claude's `tools: Read` field, and share the canonical roles/protocol/rubric. The parent owns MCP writes. Cursor's native hooks use different event/config shapes, so no Cursor hooks are registered here.
- **Grok:** native agents/hooks and Claude compatibility are documented, but the repository's `.grok-plugin/plugin.json` field contract has not been verified. It remains unchanged; do not claim native registration parity.
- **OpenCode:** `.opencode-plugin/plugin.json` remains documentation-only. OpenCode uses native agent configuration/Markdown discovery and JavaScript/TypeScript plugin hooks; this package does not install either.

Sources: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [Codex hooks](https://learn.chatgpt.com/docs/hooks), [OpenAI Claude-plugin conversion](https://developers.openai.com/plugins/guides/submit-claude-plugin), [Cursor plugin reference](https://prod.cursor.com/docs/reference/plugins), [Cursor subagents](https://prod.cursor.com/docs/subagents), [Grok extensions](https://docs.x.ai/build/features/skills-plugins-marketplaces), [OpenCode agents](https://opencode.ai/docs/agents/) and [OpenCode plugins](https://opencode.ai/docs/plugins/). Documentation/schema support is not a native runtime test or an authorization guarantee.

## Offline validation

From the checkout, run:

```sh
./scripts/install-agent-skills.sh
python3 -I -B -m unittest discover -s plugin/sharpps-knowledge/tests -v
claude plugin validate plugin/sharpps-knowledge --strict
```

The existing validator checks canonical frontmatter only; it does not test hooks, provider behavior or authorization. Offline tests check registration, shared references, helper behavior and static scenario coverage. Contract fixtures are **behavioral acceptance scenarios**, not proof a model follows prompts. No model calls, plugin installation or live operations are needed. Real multi-client discovery/delegation, live MCP activation, model-based scenario execution and provider-native behavior outside Claude remain unrun pending separate authorization.
