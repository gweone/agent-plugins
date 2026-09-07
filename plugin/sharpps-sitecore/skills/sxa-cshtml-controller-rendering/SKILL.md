---
name: sxa-cshtml-controller-rendering
description: Use when a .cshtml needs to be wired up as a Sitecore XA Controller Rendering with a custom view path (not the {Controller}/{Action} naming convention) instead of a View Rendering - typically because the View Rendering fails outside a normal page request with InvalidOperationException "Attempt to retrieve context object of type System.Web.Mvc.ViewContext from empty stack" (e.g. rendered from a Web API controller, a background job, or anywhere else that isn't Sitecore's page-rendering pipeline). Narrower than "SXA controller renderings" in general - specifically about making an existing or new .cshtml work as a Controller Rendering's view. Covers reusing the existing Sitecore.XA.Foundation.Mvc.Controllers.StandardController with no new controller code, the RenderingViewPath field, and converting an existing rendering item's template via SPE.
---

# Making a .cshtml work as a Controller Rendering (custom view path)

Scope: this skill is specifically about getting a `.cshtml` to render via a
**Controller Rendering** with a custom view path, not about SXA Controller
Renderings in general (there are many other kinds - data-bound ones with
their own model/repository, API-backed ones, etc. - out of scope here).

## Workflow: Spec -> Plan -> Execution

**Spec - ask the user if any of this is missing:**
- Is there an existing View Rendering item to convert, or is this a brand
  new rendering? If converting, get its exact item path/ID and its current
  `Path` field value (needed later - see the gotcha below).
- The target `.cshtml` path (existing file, or where to create one) -
  follow the location convention below if it doesn't already have a home.
- Tenant/Site and database (same considerations as the `sitecore` skill's
  CMS section - never assume; needed to reach the item via SPE and to know
  which database(s) to publish to afterward).

**Plan - resolve in dependency order:**
1. Confirm *why* a Controller Rendering is needed here (see "Why a View
   Rendering can fail outside a normal page request" below) - if the
   rendering only ever executes inside a normal page request, a plain View
   Rendering may be fine and none of this is necessary.
2. Resolve the Controller Rendering template ID
   (`/sitecore/templates/System/Layout/Renderings/Controller rendering`,
   `{2A3E91A0-7987-44B5-AB34-35C2D9DE83B9}`) and, if converting an existing
   item, capture its current `Path` field value before changing anything -
   it will not carry over automatically (see the gotcha below).
3. Decide the three field values to set: `Controller` (always
   `Sitecore.XA.Foundation.Mvc.Controllers.StandardController, Sitecore.XA.
   Foundation.Mvc` - no new controller), `Controller Action` (always
   `Index`), `RenderingViewPath` (the `.cshtml` path).

**Execution:**
1. If converting an existing item: change its template via SPE (static
   `TemplateManager.ChangeTemplate`, not the instance method - see gotcha
   below).
2. Set `Controller`/`Controller Action`/`RenderingViewPath` on the item via
   `New-SPESession` + `Invoke-RemoteScript` (don't just describe the
   Content Editor steps).
3. Create/verify the `.cshtml` at the location convention below, registered
   in the Feature project's `.csproj` if needed.
4. Publish the item, and rebuild whatever index/cache depends on it if
   results still look stale afterward.
5. Report back that the rendering is now dispatched as a Controller
   Rendering, and where the `.cshtml` lives.

## Why a View Rendering can fail outside a normal page request

Rendering a **View Rendering** (`.cshtml` executed via `Sitecore.Mvc.
Presentation.ViewRenderer`) requires an active `System.Web.Mvc.ViewContext`
on Sitecore's context stack (`Sitecore.Mvc.Common.ContextService`). Sitecore's
normal page-rendering pipeline pushes that context before executing views -
but anything that renders a rendering **outside** that pipeline (a Web API
controller, a background job, a custom pipeline calling `RenderVariant`
directly, etc.) never establishes it. Confirmed live:

```
InvalidOperationException: Attempt to retrieve context object of type
'System.Web.Mvc.ViewContext' from empty stack.
  at Sitecore.Mvc.Common.ContextService.Peek[T]()
  at Sitecore.Mvc.Presentation.ViewRenderer.GetHtmlHelper()
  at Sitecore.Mvc.Presentation.ViewRenderer.Render(TextWriter writer)
  at Sitecore.Mvc.Pipelines.Response.RenderRendering.ExecuteRenderer.Render(...)
```

One concrete example: SXA's own `Sitecore.XA.Feature.Search.Controllers.
SearchController` is a Web API `ApiController` (see the `sxa-search` skill) -
rendering a Rendering Variant's Component Variant Field there hits exactly
this. But the failure isn't tied to search specifically; it's any
non-page-pipeline invocation. It's also environment-dependent, not an
absolute rule - the identical View-Rendering setup can work fine on one
instance and fail on another depending on `Sitecore.Mvc`/pipeline config, so
don't assume "View Rendering can never work here" - just that it's fragile
outside a page request and **Controller Renderings don't have this
dependency**, so they're the reliable choice whenever a rendering needs to
work from a non-page context.

Also watch for this exception being silently swallowed by whatever calls
into rendering - e.g. `SearchController.GetResults`'s `catch
(InvalidOperationException)` returns a bare empty result object instead of
surfacing an error, so a real rendering crash can look identical to "no
data" from the outside unless the server log is checked.

## Use the existing StandardController - don't write a new controller

`Sitecore.XA.Foundation.Mvc.Controllers.StandardController` is a concrete
(non-abstract), already-deployed class in `Sitecore.XA.Foundation.Mvc.dll` -
part of SXA itself, so it's present on any SXA-enabled instance with no new
code required. Its `GetModel()` resolves to the framework's default
`ModelRepository`, which needs no per-rendering DI registration - it just
returns a generic `RenderingModelBase` populated from `PageContext.Current`,
`Rendering`, `DataSourceItem`, etc. Nothing to implement: its stock
`Index()` action already renders whatever view its `IRenderingViewResolver`
resolves for the rendering, which ultimately falls back to reading
`rendering.RenderingViewPath`.

**On the Controller Rendering template**
(`/sitecore/templates/System/Layout/Renderings/Controller rendering`,
`{2A3E91A0-7987-44B5-AB34-35C2D9DE83B9}`) **that field is literally named
`RenderingViewPath`** - not `Path` (that's the *View Rendering* template's
field name; the two are separate fields with different IDs, confirmed live -
don't assume they're interchangeable). Set on the rendering item:

| Field | Value |
|---|---|
| `Controller` | `Sitecore.XA.Foundation.Mvc.Controllers.StandardController, Sitecore.XA.Foundation.Mvc` |
| `Controller Action` | `Index` |
| `RenderingViewPath` | your `.cshtml`, e.g. `/Areas/v1/Views/Search/SearchResultVariant.cshtml` |

This dispatches through Controller Rendering execution (`ControllerRunner`,
not `ViewRenderer`), so it doesn't depend on a `ViewContext` being
pre-established and renders reliably even outside a page request - confirmed
live: converting an existing broken View-Rendering-based search result
variant to this exact setup fixed it immediately, with no new C# code
involved.

## Converting an existing View Rendering item to Controller Rendering via SPE

Two gotchas worth knowing, both hit live while doing this:

```powershell
$item = Get-Item -Path 'master:/path/to/the/rendering/item'
$currentTemplate = [Sitecore.Data.Managers.TemplateManager]::GetTemplate($item)
$targetTemplate = [Sitecore.Data.Managers.TemplateManager]::GetTemplate(
    [Sitecore.Data.ID]::Parse('{2A3E91A0-7987-44B5-AB34-35C2D9DE83B9}'), $item.Database)
$changes = $currentTemplate.GetTemplateChangeList($targetTemplate)
$item.Editing.BeginEdit()
[Sitecore.Data.Managers.TemplateManager]::ChangeTemplate($item, $changes) | Out-Null
$item.Editing.EndEdit() | Out-Null

$item = Get-Item -Path 'master:' -ID $item.ID
$item.Editing.BeginEdit()
$item['Controller'] = 'Sitecore.XA.Foundation.Mvc.Controllers.StandardController, Sitecore.XA.Foundation.Mvc'
$item['Controller Action'] = 'Index'
$item['RenderingViewPath'] = '/Areas/v1/Views/Search/SearchResultVariant.cshtml'  # re-set - see below
$item.Editing.EndEdit() | Out-Null
```

- Use the **static** `[Sitecore.Data.Managers.TemplateManager]::ChangeTemplate($item, $changes)`
  overload, not the instance method `$item.ChangeTemplate($changes)` -
  PowerShell's overload resolution picks the wrong overload of the instance
  method (tries to convert the `TemplateChangeList` to `TemplateItem` and
  throws) even though both exist on `Item`.
- **The old `Path` value does not carry over** - View Rendering's `Path` and
  Controller Rendering's `RenderingViewPath` are different fields (different
  IDs) even though conceptually equivalent, so `ChangeTemplate` (which
  matches by field ID) leaves the new field empty. Capture the old `Path`
  value *before* changing the template, then set it on `RenderingViewPath`
  afterward as a separate edit - it silently stays blank otherwise.
- Remember to publish the item (and rebuild the relevant search index if
  results still look stale) - a template/field change on this item alone
  doesn't help until it's live in whatever database the request actually
  resolves against.

## `.cshtml` location convention

`~/Areas/$mvc_area$/Views/{FeatureName}/{RenderingName}.cshtml` (e.g.
`~/Areas/v1/Views/Search/SearchResultVariant.cshtml`) - under that Feature
project's own Views folder, not a generic `Sitecore` subfolder, matching
where the rendering item's view-path field points. Register it as an
explicit `Content` item in the Feature project's `.csproj` if no existing
wildcard `Content Include` already covers `.cshtml` files under that Views
subfolder.

It has to live under the correct `Areas/$mvc_area$/...` path specifically,
not just anywhere convenient - `RenderingViewPath` is a virtual path that
`RenderingViewResolver.ViewExists` checks via `VirtualPathChecker.
FileExists` before using it, so it must resolve to a real file within that
Area's registered folder structure in the compiled site output. A `.cshtml`
placed outside its Area's own folder won't resolve even with the field set
correctly.
