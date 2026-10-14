---
name: knowledge-review
description: Independently review Knowledge candidates manually on request or under explicit persisted server-enforced standing consent.
---

# knowledge-review

Read [the shared participation protocol](../../references/protocol.md) before acting. User instructions and permissions override this skill.

Use the protocol for parent orchestration and actual host schemas for the backend contract; the reviewer rubric is inline in the role. Explicit manual review requires an operator request. Standing review requires supported live policy/queue/automatic schemas and enabled principal-wide consent; installing this plugin is not consent. Read policy, fetch the authorized server queue and delegate at most ten candidates per cycle to a separate reviewer. Parent alone performs guarded writes using exact candidate version, review-state revision and policy revision. Enabled standing consent permits the separate reviewer to recommend `approved_for_reuse` when complete evidence and the rubric support safe reuse, and the parent to apply it without per-candidate human confirmation. Read-only reviewer tools restrict writes, not approval recommendations. Stop on disabled, denied, stale or uncertain results. Never auto-publish or emulate unavailable auto review through manual tools.

Use the host-loaded self-contained `knowledge-reviewer` role; its inline rules are sufficient, with no external reference Reads or reference-loading acknowledgment gate. Do not send the full parent protocol/rubric to each child. Supply only minimized authorized task input and relevant live schema constraints; for review include exact candidate ID/version/state and complete evidence. The parent retains discovery, scope, consent, ACL and write guards.

If native delegation is unavailable, disclose a separate-pass fallback and use the complete compact role text from the current host-established installed plugin/skill location (`agents/knowledge-reviewer.md`, or Cursor's `agents/cursor-knowledge-reviewer.md`). If source is needed but an earlier path is stale, reload the skill using the host-supported mechanism. Do not list plugin directories, scan caches for `~g2`, guess cwd/cache paths or assume unavailable host APIs. Missing, unreadable or incomplete role instructions block the role with no draft/decision; never use brief-only review or a weaker `evidence_supported` downgrade. Prompt-level instructions are not runtime enforcement or proof of independent reruns.

Before recommending any decision, inspect `summary_truncated` and evidence completeness/count bounds. Any truncated, missing or incomplete input must escalate to the human; never automatically approve or mark evidence supported. Parent stops/escalates on `review_input_incomplete` (409) with no connector replay or manual-review downgrade to evade the guard. Actual schemas and advertised limits remain authoritative.

The [review rubric](../../references/review-rubric.md) and [backend contract reference](../../references/backend-contract.md) document the shared behavior, not child runtime dependencies. Use actual host schemas, never fixed connection prefixes or inferred authority.
