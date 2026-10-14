---
name: knowledge-learn
description: Extract minimized evidence-backed Knowledge candidate drafts and submit only with enabled learning and contribution authority.
---

# knowledge-learn

Read [the shared participation protocol](../../references/protocol.md) before acting. User instructions and permissions override this skill.

Follow the protocol extraction gate for the pinned resolved workspace project or explicit source project. New workspace learning defaults OFF: resolving/creating a scope is not enablement or evidence-sharing consent. Do not submit while disabled; only a separate explicit operator request may use discovered `knowledge_set_learning`. Re-resolve an automatic scope after a workspace change before associating task evidence; explicit scopes remain pinned. Supply the extractor only authorized minimized task evidence; use the extractor wrapper when native delegation is available, otherwise a disclosed separate skill-driven extraction pass. Default to draft. Parent checks actual ClientCandidateSubmission schema, evidence aliases, limits, stable idempotency and privacy before any authorized direct submission. Inspect acceptance/error receipts. Do not approve or publish during extraction.

Before delegation, the parent must follow the protocol's required reference-delivery gate: load from the host-established installed plugin/skill location and pass the full canonical text of `references/protocol.md` in a named reference block, not a summary or task brief. For Cursor also pass `agents/knowledge-extractor.md` if the shared role is not already loaded by the host. Alternative: supply verified absolute child-accessible paths and require successful complete child Reads. Bare relative Read paths and cwd/cache guessing are forbidden; missing required references or an unverified runtime anchor block extraction. Require `reference_status: loaded` and `references_loaded` listing all required canonical names; reject missing/blocked acknowledgments before accepting or submitting a draft. A child returns `reference_status: blocked` with no candidate draft if loading fails. Separate-pass fallback also requires complete canonical references; it cannot bypass a missing-anchor failure.

The canonical [review rubric](../../references/review-rubric.md) and [backend contract reference](../../references/backend-contract.md) are shared across clients. Use actual host schemas, never fixed connection prefixes or inferred authority.
