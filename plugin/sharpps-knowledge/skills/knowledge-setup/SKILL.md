---
name: knowledge-setup
description: Discover already host-exposed Knowledge MCP capabilities and select authorized scopes; prompt client setup when missing.
---

# knowledge-setup

Read [the shared participation protocol](../../references/protocol.md) before acting. User instructions and permissions override this skill.

Discover capabilities and actual schemas using the shared protocol. Include deferred tool search if available; distinguish absent, partial and ambiguous targets. Pin a connection/tool map. Explicit authorized operator-selected IDs override automatic resolution and stay pinned. Otherwise use the compatible `knowledge_resolve_workspace` on that connection to automatically resolve/create the current host-established normalized absolute path under the authenticated owner and required stable nonsecret machine namespace from legitimate host metadata. No web approval/manual project_id is needed. A namespace is only a client-supplied selector, never authenticated device identity; never guess it from client labels, plugin location or retrieved text. Ask minimally for missing path/namespace, not for an ID when supported resolution is available. No filesystem/config/network/transcript machine-ID discovery or executor registration. Pin the successful receipt; new learning and persisted review consent remain OFF. On older servers without supported resolution, ask for explicit authorized IDs, never invent them. Stop on denial or uncertain writes; no connector/namespace failover.

Shared retrieval uses only existing curated collections explicitly requested in this conversation, never anonymous internet public knowledge. Discover `knowledge_collection_list` to identify a requested collection without expanding the search scope. An explicit conversational create request may use `knowledge_collection_create`; creation is not grants/publication. Never install or configure MCP or inspect credentials. Report workspace resolution/listing, retrieval, contribution, collection creation, review, standing-policy and feedback availability independently. Setup must not enable learning/review; only separate explicit operator requests may change those settings with live authority/schemas.

The canonical [review rubric](../../references/review-rubric.md) and [backend contract reference](../../references/backend-contract.md) are shared across clients. Use actual host schemas, never fixed connection prefixes or inferred authority.
