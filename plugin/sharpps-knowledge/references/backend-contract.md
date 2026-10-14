# Guarded automatic-review contract (0.1.0 integration reference)

Backend coordination supplied this contract during implementation. It is not a substitute for the live host-exposed input schemas, advertised capability support or current authorization. Older servers/prepared storage may expose only base operations; do not send these payloads unless supported. Tool names below are logical names, not fixed MCP prefixes.

| Operation | Input | Result / guard |
|---|---|---|
| `knowledge_get_review_policy` | no arguments | `supported`, `enabled`, `revision`, `updated_at` |
| `knowledge_set_review_policy` | `policy: {enabled: boolean, expected_revision: integer >= 0}` | Principal-wide persisted consent; only explicit user opt-in/opt-out, optimistic revision guard |
| `knowledge_review_queue` | `request: {limit: integer 1..10 (default 10), cursor: nullable server cursor}` | `items`, `next_cursor`, `policy_revision`; each minimized item includes evidence summaries with `summary_truncated: boolean` and `review_state_revision` |
| `knowledge_auto_review` | `review: {lesson_id, version, decision, reason, policy_revision: integer >= 1, review_state_revision: integer >= 0}` | Server-enforced automatic mode, exact policy/candidate/state and live ACL guards |

The queue cursor is an opaque validated base64 timestamp/ID cursor. Reuse only server-returned cursors on the pinned connection; do not manufacture or decode them to enumerate inaccessible scopes. Read decision values and version constraints from the actual review schema rather than guessing enums.

The reviewer must escalate any truncated, missing or incomplete evidence input, including evidence-count omissions, and never recommend automatic `approved_for_reuse` or `evidence_supported` from such input. The backend conservative guard returns `review_input_incomplete` (409) for these two decisions when any sanitized evidence summary exceeds 2,000 characters or the evidence count exceeds the 100-item cap; follow any additional advertised count/completeness guards. Manual review is unchanged. Negative automatic decisions remain server-allowed, but this client reviewer conservatively escalates incomplete input rather than automatically deciding it. This bound is not permission to approve missing evidence or treat a 2,000-character prefix as the full summary. Parent stops/escalates without connector replay. Actual schemas remain authoritative.

Stop the current cycle on `review_input_incomplete`, `feature_unavailable`, `policy_conflict`, `auto_review_disabled`, `review_state_conflict`, authentication/ACL errors, stale version errors or unknown write outcomes. Never downgrade to manual review to evade an automatic guard. A human may explicitly request a separate manual review. Respect current pending state/evidence validation; auto mode does not loosen the review rubric. The server audits the same authenticated principal with automatic provenance and policy revision, not a fictional independent identity. Approval does not publish a collection. No live activation is authorized by building this plugin.
