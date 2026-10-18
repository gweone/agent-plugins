---
name: rendering-and-datasource
description: Convert hardcoded cshtml content into author-editable Sitecore datasources. Use for field design, sections, Shared parameters, repeatable option items, multilingual Standard Values, rendering-type detection, and the required design approval table.
---

# Authorable rendering and datasource design

Use for HTML-to-Sitecore conversion, not just low-level item creation.
Keep structural markup and JS/CSS hooks in code unless requested otherwise.

## Workflow

1. Inspect the source markup and invocation path. Confirm Tenant/Site,
   Feature/rendering, exact template/datasource paths, supported languages,
   and which option lists should be author-editable. Do not guess paths
   or default to View Rendering without inspecting how it is invoked.
2. Classify literals: wording, validation parameters/messages, options,
   links, or structural markup. Design grouped sections and field types.
   Technical parameters are Shared; translatable text is language-specific.
3. Define option sub-templates and folders for separate lists. Plan
   `__Standard Values` defaults for every supported language.
4. **Approval gate:** show the confirmed paths, rendering type and evidence,
   Datasource Template/Location, and a Section → Name → Type → Shared →
   Standard Value(s) table, including option sub-templates and language
   columns. Obtain explicit approval before any item creation.
5. Use [SPE remoting](../sitecore-spe-remoting/SKILL.md) and
   [template item mechanics](../sitecore-template-items/SKILL.md) to apply
   the approved design. Stop on denied access or failed authentication;
   never silently switch to hand-authored serialization. An unreachable
   instance requires the user to choose corrected access or an explicitly
   unverified hand-authored fallback.
6. Use [Unicorn serialization](../sitecore-unicorn-serialization/SKILL.md)
   to export/retrieve live-created items. Rewire the view, preserving
   Experience Editor field rendering and descendant option traversal.
7. Verify the original values render the same output; record design
   decisions and whether behavior was verified on the instance.

## Lookup

| Need | Reference |
|---|---|
| Inputs, approval/execution sequence | [Workflow](references/datasource-design.md#workflow-spec---template-design-plan-needs-approval---execution) |
| Literal classification, field types, sections, sharing, options, Standard Values | [Design steps 1–6](references/datasource-design.md#step-1-extract-the-configurable-surface-from-the-html) |
| View vs Controller, Datasource Template/Location | [Rendering detection and wiring](references/datasource-design.md#step-7-create-the-rendering---detect-view-vs-controller-wire-datasource-templatelocation) |
| Required approval table and language columns | [Approval gate](references/datasource-design.md#approval-gate-the-template-design-must-be-approved-before-creation) |
| View field reads and repeatable option lookup | [Rewiring cshtml](references/datasource-design.md#rewiring-the-cshtml-to-read-fields-instead-of-literals) |

## Related skills

- [sxa-cshtml-controller-rendering](../sxa-cshtml-controller-rendering/SKILL.md): StandardController outside page requests.
- [sxa-search-result-variants](../sxa-search-result-variants/SKILL.md): search-result presentation.
- [feature-foundation-project](../feature-foundation-project/SKILL.md): create a missing Helix module.
