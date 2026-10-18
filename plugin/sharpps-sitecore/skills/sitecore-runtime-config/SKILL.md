---
name: sitecore-runtime-config
description: Inspect Sitecore merged runtime configuration at showconfig.aspx. Use to verify App_Config Include patches, active settings, or Unicorn TriggerAutoPublishSyncedItems rather than assuming source config is live.
---

# Sitecore runtime configuration lookup

Read-only inspection of the configuration actually loaded by the instance.
This is not a general deployment or configuration-editing guide.

## Workflow

1. Confirm the instance and the exact setting/patch being investigated.
2. Resolve values with
   [sitecore-solution-config](../sitecore-solution-config/SKILL.md) and use
   the **HTTP** login in
   [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md).
   `New-SitecoreSession` takes a SecureString password; stop if login
   returns an empty session. No SPE session is needed for this lookup.
3. Fetch `/sitecore/admin/showconfig.aspx` with the authenticated
   `WebRequestSession`. Do not expose the admin page or weaken access.
4. Inspect the merged result for the relevant node/processor and compare
   it with the intended source patch. A file on disk alone is not proof
   that the patch is active.
5. Return only relevant, redacted evidence. Merged config can contain
   secrets and internal paths; do not dump it into reports or logs.

## Lookup

- [Authenticated showconfig request and Unicorn auto-publish diagnostic](references/showconfig.md)
- [SXA index/database resolver configuration](../sxa-search-index-resolution/SKILL.md)
- [Native C# pipeline processor patches](../sitecore-pipelines/SKILL.md)
