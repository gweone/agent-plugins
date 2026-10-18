---
name: sitecore-template-items
description: Create Sitecore template, section, field, base-template, rendering, and datasource items via SPE. Use for low-level New-Item mechanics, Add-BaseTemplate, field sharing, CMS item paths, or Datasource Template/Location wiring.
---

# Sitecore template and datasource item mechanics

For converting hardcoded markup into an authorable component, start with
[rendering-and-datasource](../rendering-and-datasource/SKILL.md) to design
and approve the fields. This skill handles the low-level item operations.

## Workflow

1. Confirm Tenant/Site, Feature/rendering names, exact target paths, and
   intended field/rendering design with the user; never guess the site.
   Resolve `core`/`area` via
   [sitecore-solution-config](../sitecore-solution-config/SKILL.md).
2. Read [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md), verify
   read-only connectivity, and obtain authorization before any live write.
   A remoting failure is not permission to install server packages or
   change roles. Stop on a denied call.
3. Check existing items and parent folders before creation. Create in
   dependency order: template → sections/fields → rendering → datasource.
   Do not overwrite existing items speculatively.
4. Use `New-Item` with the real Template/Template Section/Template Field
   IDs. `Add-ItemTemplateSection` and `Add-ItemTemplateField` do **not**
   exist. Use `Add-BaseTemplate` for template composition.
5. Set `Type`, `Shared`, and `Unversioned` on the field item itself;
   verify cmdlet signatures on the target with `Get-Command`/`Get-Help`.
6. Detect View vs Controller Rendering; the reference's View Rendering
   example is not a universal default. Set `Datasource Template` and
   `Datasource Location` to this task's actual template/data folder.
7. Read back the created items and wiring, then use
   [sitecore-unicorn-serialization](../sitecore-unicorn-serialization/SKILL.md)
   to export and retrieve the matching serialized tree.

## Lookup

| Need | Reference |
|---|---|
| Target inputs, dependency order, path table | [CMS conventions](references/item-creation.md#cms-content-tree-conventions-templates-renderings-datasources) |
| Template IDs, New-Item script, field sharing | [Creation example](references/item-creation.md#example-creating-a-template-rendering-and-datasource-item) |
| Controller Rendering / RenderingViewPath | [SXA controller rendering](../sxa-cshtml-controller-rendering/SKILL.md) |
| Sections, options, per-language Standard Values, approval table | [Authorable datasource design](../rendering-and-datasource/SKILL.md) |
