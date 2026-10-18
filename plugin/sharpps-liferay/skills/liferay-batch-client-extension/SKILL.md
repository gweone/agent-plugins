---
name: liferay-batch-client-extension
description: Create or debug Liferay batch client extensions, batch-engine-data.json imports, mandatory assemble packaging, Guest targeting, siteId, C_ delegates, attachments, SXP blueprints, and import verification.
---

# Liferay Batch Client Extension

A `type: batch` CX imports DTOs through Headless Batch Engine resources;
it does not create/update the Site/Group. This avoids the initializer's
system-site Group-update block, but does not guarantee every resource works.

## Workflow

1. Confirm release, company, target site, resources, and authorization boundary.
   Use [liferay-portal-source](../liferay-portal-source/SKILL.md) for external source;
   cited workspace examples/rules are consuming-workspace precedents, not plugin files.
2. Consult [resource evidence](references/resource-support.md): distinguish
   production samples, live-verified resources, and generated-but-unverified wiring.
   Objects/List Types/Workflows/Roles/Users, SXP, and document schemas have evidence;
   Documents, KB, and Pages are not proven complete batch imports here.
3. Read the [Structured Content investigation](references/structured-content-investigation.md)
   before importing Web Content: a successful task created article shells but
   left bodies empty through four attempts. Preserve that unresolved status.
4. Include the **mandatory `assemble: from: batch / into: batch` block** and
   resource scopes from [packaging](references/packaging.md). Verify `batch/`
   exists in the dist zip and the live manifest header before debugging data.
5. Use [site targeting and file format](references/site-targeting-and-format.md):
   `configuration.parameters.siteId` accepts group key, numeric ID, or ERC;
   Object Entries need both `taskItemDelegateName` locations and the `C_` prefix.
   Sort files naturally by dependency; initializer and batch multiselect shapes differ.
6. For Document Types/metadata sets, use the canonical [document-types workflow](../liferay-document-types/SKILL.md),
   not generic UPSERT/UPDATE defaults. For Object files, preserve the exact
   [attachment token/directory convention](references/attachments.md).
7. For SXP, use the [company-scoped blueprint evidence](references/resource-support.md):
   no `siteId` is needed, and nested configuration round-trips were live-verified.
8. Obtain **explicit deployment authorization**; activation runs imports immediately.
   Follow [deployment and verification](references/deployment-and-verification.md):
   dedup is bundle-`lastModified`, not content hash; rebuild for retesting.
   Check task start/finish logs and query actual resources/`dateModified` afterward.
   An Active bundle, task completion, or silence is not proof of saved content.

## Lookup

| Need | Reference |
|---|---|
| Minimal YAML, mandatory assemble, OAuth scopes, Guest rationale | [Packaging](references/packaging.md) |
| Verified resource table, SXP, unverified wiring, source greps | [Resource support](references/resource-support.md) |
| Four attempts, exact locale/field shapes, unresolved empty body | [Structured Content investigation](references/structured-content-investigation.md) |
| siteId converter, C_ delegates, JSON envelope, value shapes | [Targeting and format](references/site-targeting-and-format.md) |
| Base64 placeholder, attachments/ERC tree | [Attachments](references/attachments.md) |
| Auto-trigger, LXC distinction, dedup, logs, dateModified | [Deployment checks](references/deployment-and-verification.md) |

## Related skills

- [Site Initializer](../liferay-site-initializer/SKILL.md): broader declarative imports for ordinary sites.
- [Document Types](../liferay-document-types/SKILL.md): canonical shared schema/value import recipe.
