---
name: sitecore-unicorn-serialization
description: Export Sitecore items through Unicorn and retrieve Rainbow YAML into the workspace. Use for Export-UnicornItem vs Export-Item, predicate path coverage, PhysicalRootPath, truncated filenames, or Receive-RemoteItem downloads.
---

# Unicorn serialization and file retrieval

Use the solution's real serialization configuration, not hand-written YAML
or an assumed Sitecore CLI layout.

## Workflow

1. Inspect the solution's Unicorn XML configuration: find the predicate
   include covering the target item path and its target data store. Absence
   of `sitecore.json` does not mean serialization is unconfigured.
2. Confirm the target/configuration and authorize the export. Use
   [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md) for connection
   and live-write permission checks. Do not silently sync or publish.
3. When Unicorn covers the path, use `Export-UnicornItem -Recurse`.
   SPE's `Export-Item` produces classic `.item` text, not Rainbow YAML;
   consider it only when no Unicorn or equivalent serialization covers
   that path. Verify installed commands on the actual target.
4. Resolve the live `ITargetDataStore.InnerDataStore.PhysicalRootPath`.
   It is a **field**, not a property; config tokens are not resolved paths.
5. List actual exported filenames: Rainbow may truncate long names.
   Export runs on the server filesystem, not necessarily this workspace.
6. If remote, retrieve files client-side with `Receive-RemoteItem`, preserving
   the relative tree. Inspect local destinations before replacing files;
   do not overwrite unrelated workspace changes.
7. Compare retrieved IDs, field sharing, ordering, and paths with existing
   serialization, then inspect the diff. No transfer is needed when the
   export already wrote to the workspace filesystem.

## Lookup

| Need | Reference |
|---|---|
| Coverage, Export-UnicornItem vs Export-Item | [Export mechanism](references/export-and-retrieve.md#serializing-an-item-to-disk---check-for-unicorn-first-dont-default-to-export-item) |
| Resolve the live serialization root | [PhysicalRootPath](references/export-and-retrieve.md#finding-where-unicorn-actually-wrote-the-files) |
| Unexpected or missing YAML filenames | [Rainbow filename truncation](references/export-and-retrieve.md#filename-truncation---a-real-item-name-doesnt-always-match-its-filename) |
| Remote server → workspace download | [Retrieve exported files](references/export-and-retrieve.md#retrieving-the-exported-files-onto-the-machine-that-needs-them) |

The reference's Maybank paths and Core.Website configuration are examples,
not defaults for the current solution.
