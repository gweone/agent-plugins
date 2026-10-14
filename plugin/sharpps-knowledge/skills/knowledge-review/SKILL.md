---
name: knowledge-review
description: Independently review Knowledge candidates manually on request or under explicit persisted server-enforced standing consent.
---

# knowledge-review

Read [the shared participation protocol](../../references/protocol.md) before acting. User instructions and permissions override this skill.

Read the protocol, reviewer rubric and backend contract reference. Explicit manual review requires an operator request. Standing review requires supported live policy/queue/automatic schemas and enabled principal-wide consent; installing this plugin is not consent. Read policy, fetch the authorized server queue and delegate at most ten candidates per cycle to a separate reviewer. Parent alone performs guarded writes using exact candidate version, review-state revision and policy revision. Enabled standing consent permits the separate reviewer to recommend `approved_for_reuse` when complete evidence and the rubric support safe reuse, and the parent to apply it without per-candidate human confirmation. Read-only reviewer tools restrict writes, not approval recommendations. Stop on disabled, denied, stale or uncertain results. Never auto-publish or emulate unavailable auto review through manual tools.

Before recommending any decision, inspect `summary_truncated` and evidence completeness/count bounds. Any truncated, missing or incomplete input must escalate to the human; never automatically approve or mark evidence supported. Parent stops/escalates on `review_input_incomplete` (409) with no connector replay or manual-review downgrade to evade the guard. Actual schemas and advertised limits remain authoritative.

The canonical [review rubric](../../references/review-rubric.md) and [backend contract reference](../../references/backend-contract.md) are shared across clients. Use actual host schemas, never fixed connection prefixes or inferred authority.
