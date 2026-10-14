---
name: knowledge-status
description: Report pinned Knowledge capabilities, scopes, learning/review policy and receipts; record version-specific reuse feedback.
---

# knowledge-status

Read [the shared participation protocol](../../references/protocol.md) before acting. User instructions and permissions override this skill.

Report only observed pinned capabilities, resolved workspace path/namespace/project receipt or explicit operator-selected scopes, and receipts. Read workflow/policy only where supported; do not change settings. Clearly distinguish unsupported, disabled and denied capabilities; new workspace learning and persisted review consent default OFF independently. For an explicit workspace list/status request, discover `knowledge_list_workspaces` and its live `request` schema (optional namespace, limit at most 50, opaque server cursor). Listing does not authorize scope changes, adoption of `project.workspace` metadata or deleted-scope recreation. For a conversation-requested curated collection, discover `knowledge_collection_list` to clarify authorized metadata, not to search all collections. Record schema-valid version-specific feedback for findings actually reused. Status is read-only: no grants, project/collection creation, deletion, learning/policy enablement or publication to repair a gap. If scope is missing, report it and route to setup separately; only setup's supported resolver branch may automatically resolve/create the current workspace. Explicit collection creation belongs to a separate conversational create request, never a status side effect.

The canonical [review rubric](../../references/review-rubric.md) and [backend contract reference](../../references/backend-contract.md) are shared across clients. Use actual host schemas, never fixed connection prefixes or inferred authority.
