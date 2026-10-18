---
name: liferay-site-initializer
description: Create, debug, or inspect Liferay Site Initializers, siteInitializer client extensions, resource folders, ERC targeting, tokens, pages, documents, KB, Objects, and SXP blueprint imports.
---

# Liferay Site Initializer

Provision a new or ordinary existing site from declarative `site-initializer/`
resources. Prefer the Client Extension form on 7.4+/Quarterly unless custom
Java requires an OSGi `SiteInitializer`; both use `BundleSiteInitializer`.

## Workflow

1. Confirm the target release, company, site ERC, and intended resources.
   Resolve source with [liferay-portal-source](../liferay-portal-source/SKILL.md).
   Source and consuming-workspace examples in the references are external
   precedents, not files in this plugin repository.
2. **Never target system-required sites** (`L_GUEST`, Global, Control Panel).
   Read the [system-site failures](references/limitations.md#system-required-sites);
   use [batch](../liferay-batch-client-extension/SKILL.md) only for verified resources.
3. Choose the packaging form and inspect [ERC targeting](references/packaging-and-targeting.md).
   Existing ordinary ERCs target that site in place; missing ERCs create sites.
   The CX activates automatically: there is no separate initializer-selection step.
4. Map files to the [supported resource contract](references/resources.md).
   Preserve sibling folder/file metadata, KB `articleBody` disambiguation,
   layout definitions, and DXP/Commerce extension-point requirements.
5. For custom Document Types, bootstrap [document schemas and values](../liferay-document-types/SKILL.md)
   first. Initializers cannot create those schemas; do not substitute Expando
   when the consumer expects `documentType.contentFields`.
6. Verify [tokens and dependency order](references/tokens-and-source-verification.md)
   against the actual checkout. Unmet dependencies can leave literal tokens;
   a resource table is not proof that the running release supports it.
7. Review [nightly-build limitations](references/limitations.md), including
   relationship ERCs, multiselect shapes, folder visibility, and REST paths.
   These findings require re-verification on other builds.
8. Obtain **explicit deployment authorization** before build-and-deploy,
   redeploy, OSGi mutation, or restart. Activation writes immediately.
   Follow [lifecycle and bounded-log checks](references/deployment-and-lifecycle.md);
   `Active`, a processed zip, or no errors alone does not prove initialization.

## Lookup

| Need | Reference |
|---|---|
| YAML, scopes, nested zip vs LXC artifacts, targeting | [Packaging](references/packaging-and-targeting.md) |
| Resource table, KB folders/articles, page/Widget examples | [Resources](references/resources.md) |
| Token table, engine greps, fixtures | [Tokens and source verification](references/tokens-and-source-verification.md) |
| System-site prohibition, nightly bugs, permission gaps | [Limitations](references/limitations.md) |
| Build/deploy commands, abort semantics, stuck uninstall | [Deployment lifecycle](references/deployment-and-lifecycle.md) |

## Related skills

- [Batch Client Extension](../liferay-batch-client-extension/SKILL.md): REST imports without Group updates.
- [Document Types](../liferay-document-types/SKILL.md): shared schema bootstrap and document metadata.
- [Data Engine form rules](../liferay-data-engine-form-rules/SKILL.md): related form-rule work.
