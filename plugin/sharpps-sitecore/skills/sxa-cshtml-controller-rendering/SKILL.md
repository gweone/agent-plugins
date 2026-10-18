---
name: sxa-cshtml-controller-rendering
description: Use to wire a cshtml view to an SXA Controller Rendering with StandardController and RenderingViewPath, or convert a View Rendering via SPE when rendering outside a page request fails with an empty ViewContext stack.
---

# SXA cshtml Controller Rendering

Keep an existing or new `.cshtml` as the view of SXA's stock
`StandardController`; no custom controller code is needed.
This is not a guide to all SXA controller/model/repository patterns.
No broad Sitecore skill is a prerequisite.

## Lookup

- [Spec → Plan → Execution](references/controller-rendering.md#workflow-spec---plan---execution)
  — required inputs, dependency order, publication, and reporting.
- [Why View Rendering can fail](references/controller-rendering.md#why-a-view-rendering-can-fail-outside-a-normal-page-request)
  — empty `ViewContext` stack, environment differences, swallowed failures.
- [StandardController and exact fields](references/controller-rendering.md#use-the-existing-standardcontroller---dont-write-a-new-controller)
  — template ID, model/view resolution, and field values.
- [SPE conversion recipe](references/controller-rendering.md#converting-an-existing-view-rendering-item-to-controller-rendering-via-spe)
  — static `TemplateManager.ChangeTemplate` and field migration gotchas.
- [View location and project registration](references/controller-rendering.md#cshtml-location-convention)
  — Area folder, virtual path validation, and `.csproj` inclusion.

## Implementation checklist

1. Confirm the non-page request need. A View Rendering may be fine during
   normal page rendering; outside it, behavior can vary by environment.
2. Ask for the existing rendering path/ID or new-rendering intent,
   `.cshtml` path, Tenant/Site, database, and publish targets.
3. Before conversion, capture the existing `Path` value. It does not migrate
   to `RenderingViewPath`: these fields have different IDs.
4. Use the static `TemplateManager.ChangeTemplate($item, $changes)` overload;
   the instance method can resolve to the wrong PowerShell overload.
5. Set `Controller` to
   `Sitecore.XA.Foundation.Mvc.Controllers.StandardController, Sitecore.XA.Foundation.Mvc`,
   `Controller Action` to `Index`, and `RenderingViewPath` to the view path.
6. Create/verify the view under its Feature's Area Views folder and ensure
   project inclusion. The virtual path must exist in compiled site output.
7. Execute item edits via `New-SPESession` + `Invoke-RemoteScript`, publish
   to the database the request uses, and rebuild dependent indexes/caches
   if still stale. Check server logs when empty results hide rendering errors.
8. Report Controller Rendering dispatch and the `.cshtml` location.

## Related skills

- [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md)
  — authenticated remote execution.
- [sitecore-template-items](../sitecore-template-items/SKILL.md)
  and [rendering-and-datasource](../rendering-and-datasource/SKILL.md)
  — supporting rendering/template/datasource items.
- [sxa-search-result-variants](../sxa-search-result-variants/SKILL.md)
  — Component Variant Fields invoking this rendering per search result.
- [sxa-search](../sxa-search/SKILL.md) and
  [sxa-search-index-resolution](../sxa-search-index-resolution/SKILL.md)
  — endpoint behavior and the database/index serving the request.
