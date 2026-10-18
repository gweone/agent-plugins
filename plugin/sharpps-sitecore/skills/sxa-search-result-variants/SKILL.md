---
name: sxa-search-result-variants
description: Use to create or debug native Sitecore SXA search result Html with the v/VariantID parameter, Rendering Variant items, Component Variant Fields, search-result cshtml views, and Results Variant Selector.
---

# SXA search result variants

Use this skill for the Rendering Variant behind each search result's `Html`.
The `v` parameter is a Variant Definition item ID, not a search-specific
rendering format. No broad Sitecore skill is a prerequisite.

## Lookup

- [Variant rendering pipeline](references/result-variants.md#how-vvariantid-renders-each-results-html)
  — parsing typed nodes and executing `renderVariantField` per result.
- [Spec → Plan → Execution](references/result-variants.md#workflow-spec---plan---execution-creating-a-search-result-variant)
  — dependency order, remote item creation, and IDs to report.
- [Locations and template IDs](references/result-variants.md#where-these-variant-items-live-in-the-content-tree)
  — Search Results group and Variant Definition items.
- [Component Variant Field and cshtml example](references/result-variants.md#component-variant-field-reusing-a-rendering-for-each-result)
  — rendering context, view location, project registration, and JSON shape.
- [Results Variant Selector](references/result-variants.md#results-variant-selector-picking-among-multiple-result-variants)
  — `AvailableVariants` and client-side `v` selection.

## Implementation checklist

1. Ask for Tenant/Site, variant name, and plain field nodes versus a
   Component Variant Field. Check whether the referenced rendering exists.
2. Decide whether an existing Search Scope is sufficient; do not create a
   narrowed scope automatically or guess its `ScopeQuery`.
3. For a Component Variant Field, create/verify a Controller Rendering
   using the existing SXA `StandardController`, not a new controller.
   View Renderings outside a page request can fail with an empty
   `ViewContext` stack and be silently swallowed into empty results.
4. Put the view under the Feature's
   `~/Areas/$mvc_area$/Views/{FeatureName}/{RenderingName}.cshtml`;
   register it in the `.csproj` if not already covered.
5. Create the Variant Definition and child field nodes using SPE.
   `RenderingItem` must point to a real rendering item.
6. Keep datasource configuration distinct from the current result:
   `RenderingContext.Current.PageContext.Item` is the search result item.
7. Report the variant ID (`v`) and any newly created scope ID (`s`).
   Native results return pre-rendered HTML strings, not per-field JSON.

## Related skills

- [sxa-search](../sxa-search/SKILL.md) — API parameters, scope rules, responses.
- [sxa-search-index-resolution](../sxa-search-index-resolution/SKILL.md)
  — database/index selection and authenticated testing.
- [sxa-cshtml-controller-rendering](../sxa-cshtml-controller-rendering/SKILL.md)
  — `StandardController`, `RenderingViewPath`, and SPE conversion recipe.
- [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md)
  — `New-SPESession` and `Invoke-RemoteScript` execution.
- [sitecore-template-items](../sitecore-template-items/SKILL.md)
  and [rendering-and-datasource](../rendering-and-datasource/SKILL.md)
  — supporting templates, rendering items, and datasource workflow.
