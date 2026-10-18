# SXA search result variants

## How `v`/`VariantID` renders each result's `Html`

Each result's `Html` is produced by SXA's general-purpose **Rendering
Variants** mechanism (`Sitecore.XA.Foundation.Variants.Abstractions` /
`Sitecore.XA.Foundation.RenderingVariants` - the same engine used by List
renderings etc.), just applied per search-result item instead of per-list-item:

1. A Rendering Variant is a Sitecore item tree of typed field nodes -
   `VariantField`, `VariantText`, `VariantSection`, `VariantPlaceholder`,
   `VariantScriban`, `VariantDate`, `VariantReference`,
   `VariantResponsiveImage`, `VariantHtmlTag`, `VariantToken`, `VariantModel`,
   `VariantQuery`, `VariantEditFrame`, etc. (each with its own template ID).
2. `SearchController.GetResults` resolves `Item variant =
   Context.Database.GetItem(model.VariantID)` - i.e. the item ID passed via
   the `v` query param.
3. For each result item, `new Result(searchItem, variant)` calls
   `IVariantRenderer.RenderVariant(variantItem, dataItem)`, which parses the
   variant item into `BaseVariantField`s (`IVariantFieldParser.ParseVariantFields`)
   and, for each field, runs the `renderVariantField` core pipeline (one
   processor per field type - `RenderText`, `RenderHtmlTag`, `RenderScriban`,
   `RenderPlaceholder`, etc. in
   `RenderingVariants.Pipelines.RenderVariantField`) - concatenating each
   field's output into `Result.Html`.

So `v` must be the item ID of a Rendering Variant definition item (built the
same way as any other SXA rendering variant), not something search-specific.

### Workflow: Spec -> Plan -> Execution (creating a search result variant)

**Spec - ask the user if any of this is missing:**
- Tenant/Site (see [sitecore-template-items](../../sitecore-template-items/SKILL.md) - never assume)
- Variant name
- Whether it's plain field-based (`VariantText`/`VariantField`/etc.) or a
  **Component Variant Field** reusing a Rendering - if the latter, it must be
  a Controller Rendering, not a View Rendering and not a new custom
  controller (see the [sxa-cshtml-controller-rendering](../../sxa-cshtml-controller-rendering/SKILL.md) skill for the exact
  fields/why), and check whether that rendering (and its backing
  Feature-layer template/rendering item, per [sitecore-template-items](../../sitecore-template-items/SKILL.md)
  and [rendering-and-datasource](../../rendering-and-datasource/SKILL.md)) already exists or needs to be created first
- Whether this needs its own Search Scope (a new `s` value) or can reuse the
  site's existing default scope - don't assume a new scope is needed, see
  [Search Scope](../../sxa-search/references/api-and-query.md#search-scope-the-item-behind-the-s-param)

**Plan - resolve in dependency order:**
1. If using a Component Variant Field and the rendering doesn't exist yet:
   run [sitecore-template-items](../../sitecore-template-items/SKILL.md) and
   [rendering-and-datasource](../../rendering-and-datasource/SKILL.md) for the template/rendering/datasource workflow first,
   creating it directly as a Controller Rendering per the
   [sxa-cshtml-controller-rendering](../../sxa-cshtml-controller-rendering/SKILL.md) skill - the Component Variant Field's
   `RenderingItem` field needs a real rendering item ID to point at
2. `.cshtml` location (if Component Variant Field): `~/Areas/$mvc_area$/
   Views/{FeatureName}/{RenderingName}.cshtml` - see below
3. Variant item location: `{sxa-site}/Presentation/Rendering Variants/Search
   Results/{variant name}` - see below
4. Child field node(s) under the variant item - a `VariantComponentField`
   (`{1151B2A9-08AF-4F4D-A892-C2CC9A92EA6A}`) with `RenderingItem` set to the
   rendering from step 1, or plain `VariantText`/`VariantField`/etc. nodes
5. Only if a new scope was decided in Spec: a `Scope` item under
   `{sxa-site}/Settings/Scopes/{scope name}` with its `ScopeQuery` field -
   see [Search Scope](../../sxa-search/references/api-and-query.md#search-scope-the-item-behind-the-s-param)

**Execution:**
1. Create the `.cshtml` file and register it in the `.csproj` (see below)
2. Create the variant item and its field node(s), and the scope item if
   needed, via `New-SPESession` + `Invoke-RemoteScript` (see
   [sitecore-spe-remoting](../../sitecore-spe-remoting/SKILL.md) - don't just describe the Content
   Editor steps)
3. Report back the variant item's ID (the `v` value) and, if created, the
   scope item's ID (the `s` value) to pass to `/sxa/search/results`

### Where these variant items live in the content tree

`{sxa-site}/Presentation/Rendering Variants/Search Results` - i.e.
`/sitecore/content/{Tenant}/{Site}/Presentation/Rendering Variants/Search
Results/{variant name}`. Author/edit the variant's field nodes there in the
Rendering Variants editor; its item ID is what gets passed as `v` (or listed
in a Results Variant Selector's `AvailableVariants`).

Live-verified template IDs (from an existing "Search Results" variant group
on `sitecorex41.dev.wsc`):

| Item | Template name | Template ID |
|---|---|---|
| The group folder itself (e.g. "Search Results") | `Variants` | `{E1A3B30C-77BC-4F6C-A008-D01B3371235D}` |
| An individual variant (e.g. "horizontal") | `Variant Definition` | `{FB3E3034-33F8-4CE8-BE98-DD05010F4C22}` |

Like Scopes, the group folder is normally pre-provisioned by SXA (this
instance already had "Search Results", "Promo", "POI", etc. groups) - usually
only the individual `Variant Definition` item needs creating.

### Component Variant Field: reusing a Rendering for each result

The `RenderComponentField` processor (`SupportedType = VariantComponentField`)
runs the referenced Rendering through the normal `mvc.getRenderer` /
`mvc.renderRendering` pipelines, and pushes a `PageContext` whose `Item` is
the current variant data item (the search result) before rendering it.

**Use a Controller Rendering, not a View Rendering, for the target of a
Component Variant Field used in search.** `/sxa/search/results` is served by
`SearchController : ApiController` - a Web API request, not a normal MVC
page-rendering pipeline request - and rendering a View Rendering outside a
page request is fragile (can throw `InvalidOperationException: ViewContext
from empty stack`, confirmed live, and the exception gets silently
swallowed into an empty result rather than surfacing as an error). See the
[sxa-cshtml-controller-rendering](../../sxa-cshtml-controller-rendering/SKILL.md) skill for the full why/how - it covers reusing
the existing `Sitecore.XA.Foundation.Mvc.Controllers.StandardController`
(no new controller code) with the Controller Rendering's `RenderingViewPath`
field, and the exact steps to convert an existing rendering item via SPE.
That skill's guidance isn't search-specific, but it's exactly what a
Component Variant Field's target rendering needs here.

If you do use a View Rendering anyway, inside its `.cshtml`:

- `RenderingContext.Current.Rendering.Item` - the rendering's own
  **Datasource** item (whatever was set on the Component Variant Field's
  `Data Source` rendering parameter - typically a shared config/template item
  holding fallback values, link targets, etc., not the search result itself)
- `RenderingContext.Current.PageContext.Item` - the **search result item**
  (`args.Item` from `RenderVariant(variantItem, item)` - each entry from the
  search results, i.e. what `PageContext.Item` gets pushed to)

The `.cshtml` file itself belongs under that Feature project's own Views
folder, not a generic `Sitecore` subfolder:
`~/Areas/$mvc_area$/Views/{FeatureName}/{RenderingName}.cshtml` (e.g.
`~/Areas/v1/Views/Search/SearchResultVariant.cshtml`) - matching where the
View Rendering item's `Path` field points. Register it as an explicit
`Content` item in the Feature project's `.csproj` if no existing wildcard
`Content Include` already covers `.cshtml` files under that Views subfolder.

Example `.cshtml` (search result card, reused via a Component Variant Field):

```cshtml
@using Sitecore.Mvc
@using Sitecore.Mvc.Presentation
@using Sitecore.Data.Items
@using Sitecore.Links
@{
    // Datasource of the View Rendering itself (set via the Component Variant Field's
    // "Data Source" rendering parameter) - shared fallback config, not the result item.
    Item datasource = RenderingContext.Current.Rendering.Item;

    // The search result item for this row, pushed by RenderVariant(variantItem, item).
    Item result = RenderingContext.Current.PageContext.Item;
    string resultUrl = LinkManager.GetItemUrl(result);
}
<div class="search-result-variant">
    @Html.Sitecore().Field("Image", result)
    <div class="search-result-variant__body">
        <h3 class="search-result-variant__title">
            <a href="@resultUrl">@Html.Sitecore().Field("Title", result)</a>
        </h3>
        <p class="search-result-variant__snippet">@Html.Sitecore().Field("Description", result)</p>
        <span class="search-result-variant__url">@resultUrl</span>
    </div>
</div>
```

This is why `ResultSet.Results[].Html` in the JSON response is a plain
**string of pre-rendered markup**, not structured JSON - the server executes
this `.cshtml` per result (via the Component Variant Field -> View Rendering
chain above) and embeds its output verbatim:

```json
{
  "TotalTime": 0,
  "QueryTime": 0,
  "Signature": "string",
  "Index": "string",
  "Count": 0,
  "Results": [
    {
      "Id": "string",
      "Language": "string",
      "Path": "string",
      "Url": "string",
      "Name": "string",
      "Html": "string"
    }
  ]
}
```

(`RenderVariantField.JSON` processors exist as a separate pipeline group for
headless/JSS scenarios that need structured JSON per field instead of an
HTML string - not what the native `/sxa/search/results` endpoint uses.)

### Results Variant Selector (picking among multiple result variants)

`ResultsVariantSelectorController`/`ResultsVariantSelectorRepository` is a
separate component that renders a UI widget letting a visitor pick among
several result-display variants (e.g. grid vs. list). Its `AvailableVariants`
rendering parameter is a pipe (`|`) separated list of Rendering Variant item
IDs; the repository resolves each into a `ResultsVariantModel`
(`DataVariant` = item ID, `DataVariantIndex`, a `CssClasses` marking the
active one) for the widget to render `data-variant="{id}"` options that
client-side JS uses to drive the `v` param on subsequent
`/sxa/search/results` calls.
