---
name: sxa-search
description: Use when working with Sitecore XA (SXA)'s native search feature - Sitecore.XA.Feature.Search.Controllers.SearchController and the /sxa/search/* Web API endpoints. Covers routes, query string params, and response shapes for results/facets/suggestions.
---

# Sitecore XA Feature Search (native)

`Sitecore.XA.Feature.Search.Controllers.SearchController` is SXA's own search
Web API controller, routed by SXA per-site as
`{site-virtual-folder}/sxa/{controller}/{action}`, e.g. `/sxa/search/results`.
Web API (not MVC) - query string only, JSON only.

| Action | Route | Model binder | Response |
|---|---|---|---|
| `GetResults` | `/sxa/search/results` | `QueryModel` | `ResultSet` |
| `GetFacets` | `/sxa/search/facets` | `FacetsModel` | `FacetSet` |
| `GetSuggestions` | `/sxa/search/suggestions` | `QueryModel` | `SuggestionsSet` |

## Query string parameters

| Param | Used by | Binds to | Meaning |
|---|---|---|---|
| `q` | all | `Query` | search term; server truncates to 100 chars |
| `s` | all | `ScopesIDs` | `,`/`\|`-separated item IDs whose `ScopeQuery` field defines the search scope |
| `l` | all | `Languages` | `,`/`\|`-separated language codes |
| `sig` | all | `Signature` | opaque client token, echoed back HTML-encoded |
| `sc_site` | all | `Site` | site name, drives home item / index resolution |
| `itemid` | all | `ItemID` | context item; drives `IIndexResolver` + scope tokens |
| `g` | all | `Coordinates` | `lat\|lng` (normalized to `lat,lng`); presence alone flips the request into geolocation mode |
| `o` | Results/Suggestions | `Sortings` | `\|`-separated sort fields, e.g. `field1\|-field2` |
| `e` | Results/Suggestions | `Offset` | paging offset (int) |
| `p` | Results/Suggestions | `PageSize` | page size (int), default `20` |
| `v` | Results/Suggestions | `VariantID` | rendering variant used to render each result's `Html` |
| `f` | Facets | `Facets` | `,`/`\|`-separated facet field keys to compute |

Facet filter widgets (checklist/range/radius/etc.) append their own query
params, read independently by `SearchService.GetQuery` via
`Context.Request.QueryString` - not part of the model binders above.

### How to specify site and database on a search request

Verified live against a real instance (`sitecorex41.dev.wsc`, Sitecore XM
10.x) - same query, only the session differed:

| Session | Resulting `Index` |
|---|---|
| Unauthenticated / bad credentials | `sitecore_sxa_web_index` |
| Authenticated as `admin` (Administrator) | `sitecore_sxa_master_index` |

```powershell
$sp = ConvertTo-SecureString $Password -AsPlainText -Force
$webSession = New-SitecoreSession -Url $Url -Username $Username -Password $sp

$query = "/sxa/search/results?sc_site=$SiteName&sc_database=$Database&itemid=$ItemId&v=$VariantId&p=5&e=0"
Invoke-WebRequest -Uri "$Url$query" -WebSession $webSession -UseBasicParsing
```

- `sc_site` - plain public param (`Site` on `BaseModel`), works for anyone,
  no authentication needed. Drives home-item/predicate scoping (see
  `PageOrMediaPredicate` below) - **not** the same thing as choosing a
  database. It's also **not** what determines which site handles the request
  in the first place (standard Sitecore site resolution - host name + virtual
  folder - already ran before the search controller does), and it only
  reaches index resolution as an edge-case disambiguator (see "How `sc_site`
  actually reaches this" below) - in the common non-overlapping-sites case it
  has no effect there at all. Live-verified on `sitecorex41.dev.wsc`: with
  the `Demo` site bound to hostname `*` / virtual folder `/` (the only site
  matching that host, so no ambiguity to disambiguate), `/sxa/search/results`
  returned byte-identical results with and without `sc_site=Demo` - omitting
  it is safe whenever the request already lands on the right site through
  its own URL and that site's content isn't nested under another site's root.
- `sc_database` - **not** part of the SXA search request models at all; it's
  core Sitecore's own `sc_database` query string switch
  (`Sitecore.Pipelines.HttpRequest.DatabaseResolver`, part of the standard
  `httpRequestBegin` pipeline, evaluated before the search controller ever
  runs). It only takes effect when the request is authenticated as an
  Administrator or a member of `Sitecore Client Users` - an anonymous/
  unauthenticated call silently ignores it and the database stays whatever
  the site is configured for (typically `web`). That's why the example above
  goes through `New-SitecoreSession`'s `$webSession` rather than a bare
  `Invoke-WebRequest` - a plain anonymous fetch (browser JS, curl, etc.)
  cannot exercise `sc_database` at all.

Full details on both mechanisms - including why there's no equivalent
`?index=` override - are below.

### No way to specify the index name directly - it's always server-resolved

`QueryModel`/`FacetsModel`/`BaseModel` (see the param table above) have no
`Index`/`IndexName` property, and `BaseModelBinder<T>` only ever binds `q`,
`s`, `l`, `sig`, `sc_site`, `itemid`, `g` - there's no query string key that
picks an index directly. Resolution is entirely server-side, via
`IIndexResolver.ResolveIndex(contextItem)` (`Sitecore.XA.Foundation.Search.
Services.IndexResolver`, decompiled and read directly - not just inferred):

```csharp
public ISearchIndex ResolveIndex(Item contextItem)
{
    if (contextItem != null)
    {
        SiteInfo siteInfo = SiteInfoResolver.GetSiteInfo(contextItem);
        if (siteInfo != null && siteInfo.Properties.AllKeys.Contains("indexes"))
        {
            // try "{db}/{lang}" then "{db}/*" as a key into the site's
            // "indexes" property (a query-string-shaped value); use the
            // matched value directly as the index name if it exists
            // ... else fall through to sitecore_sxa_{db}_index if it exists
        }
    }
    return ResolveDefautIndexes(); // page-mode-based default, see below
}
```

1. If `contextItem` is `null` (no `itemid`, or the ID doesn't resolve) -
   **skip straight to step 3**, no site/database-specific index is even
   attempted.
2. Else, resolve the item's site via `SiteInfoResolver.GetSiteInfo
   (contextItem)` (see below - **this is where `sc_site` can actually feed
   in**, contrary to what it might look like from the query string alone).
   If that site has an `indexes` site-definition property (a
   query-string-shaped value, e.g. `indexes="master/en=my_en_index&master/*=
   my_fallback_index"`), look up the key `{db}/{lang}` first (`db` =
   `contextItem.Database.Name`, `lang` = the item's own IETF language tag,
   both lowercased - **yes, genuinely per-language**), then `{db}/*` as a
   language-agnostic fallback key; the matched value is used directly as the
   index name if that index exists. Else try `sitecore_sxa_{db}_index`.
3. Else a page-mode-based default (`IPageMode.IsNormal`):
   `sitecore_sxa_web_index` (normal/live mode) or `sitecore_sxa_master_index`
   (edit/preview mode). If even those named indexes don't exist,
   `ResolveSitecoreIndex()` falls back to `ContentSearchManager.GetIndex(
   (SitecoreIndexableItem)DatabaseRepository.GetContentDatabase().
   GetRootItem())` - note this passes the **database's root item**, not the
   original `contextItem`.

#### The real last-resort mechanism: core Sitecore's `contentSearch.getContextIndex` pipeline

`ContentSearchManager.GetIndex(IIndexable)` (used by step 3's final
fallback above) isn't itself SXA - it's core Sitecore's own generic
"which index owns this item" resolution, and unlike everything above, it
*is* a genuinely configurable Sitecore pipeline: `GetContextIndexName`
runs `pipeline.Run("contentSearch.getContextIndex", args)`
(`PipelineBasedSearchProvider`), live-confirmed in `Sitecore.ContentSearch.
config` on `sitecorex41.dev.wsc`:

```xml
<contentSearch.getContextIndex>
  <processor type="Sitecore.ContentSearch.Pipelines.GetContextIndex.FetchIndex, Sitecore.ContentSearch">
    <excludedIndexes hint="list">
    </excludedIndexes>
  </processor>
</contentSearch.getContextIndex>
```

The default (and only shipped) processor, `FetchIndex`, decompiled:
1. Takes every registered index (`ContentSearchManager.Indexes`) not in
   `excludedIndexes`.
2. Filters to indexes with at least one crawler that doesn't exclude this
   item (i.e. whose `<locations>` root/database config actually covers it).
   If none match that way, falls back to `index.Covers(item)` instead.
3. If exactly one candidate index remains, uses it. If several remain
   (e.g. overlapping crawler roots), ranks them via `IContextIndexRankable.
   GetContextIndexRanking` (lower wins) and picks the best.
4. If zero candidates match, logs `"There is no appropriate index for
   {path} - {id}. You have to add an index crawler that will cover this
   item"` and returns `null` (which surfaces as `IndexNotFoundException`
   from `ContentSearchManager.GetIndex`).

This is the mechanism to add a custom processor to (or edit `excludedIndexes`
on) if you need to change how the *database-root* fallback resolves - not
`IIndexResolver`, which only ever calls into this as a last resort and
never for the SXA-named indexes above it.

#### How `sc_site` actually reaches this (and usually doesn't)

`SiteInfoResolver.GetSiteInfo(item)` (`Sitecore.XA.Foundation.Multisite`,
also decompiled) resolves the item's site almost entirely by **content-tree
path**, not by `sc_site`:

1. `DiscoverPossibleSites(item)` - every site whose `RootPath` is a prefix of
   the item's path, longest-`RootPath`-first.
2. **If that list has 0 or 1 entries, it returns immediately** - `sc_site` is
   never even read. This is the common case for a normal single-site-per-path
   solution, which is why the live test above (single site, unambiguous path)
   showed identical results with and without `sc_site`.
3. Only when an item's path matches **more than one** site's `RootPath`
   (nested/overlapping site trees - e.g. a shared content area under two
   different site roots) does it read `sc_site` from the query string
   (`ResolveSiteFromQuery`) as a tie-breaker among the already-matching
   candidates, before falling further back to language/context-site/request
   host-based tie-breaks.

So the accurate statement is: **`sc_site` can influence index resolution,
but only as a disambiguator when `itemid` alone is genuinely ambiguous
between multiple sites' content trees** - it's never the primary driver, and
in a typical solution with non-overlapping site roots it has no effect on
`ResolveIndex` at all (though it still affects `GetHomeItem` for predicate
scoping regardless - see above).

So the only *indirect* lever a client has over which index gets queried is
`itemid` (via that item's resolved site's `indexes` config) and, in the
overlapping-site edge case above, `sc_site` - there's no `?index=` override.

#### Going beyond site-level: overriding `IIndexResolver` for per-item/bucket resolution

The stock `IndexResolver`'s `indexes` property is keyed per **site + database
+ language** only - it has no per-item granularity. If a solution needs a
specific item (or bucket) to resolve to its own index regardless of site
config, the fix is a custom `IIndexResolver` DI override, **inheriting the
stock `IndexResolver`** so its site/page-mode fallback chain above still
works as the last resort - not a from-scratch reimplementation. This
solution's own `SharpPS.Sitecore.ContentSearch.XA.Services.
BucketableIndexResolver` is a real example of this pattern (read directly
from source, not decompiled - it's part of this codebase):

```xml
<register
    serviceType="Sitecore.XA.Foundation.Search.Services.IIndexResolver, Sitecore.XA.Foundation.Search"
    implementationType="SharpPS.Sitecore.ContentSearch.XA.Services.BucketableIndexResolver, SharpPS.Sitecore.ContentSearch.XA"
    lifetime="Singleton"
    patch:instead="*[@serviceType='Sitecore.XA.Foundation.Search.Services.IIndexResolver, Sitecore.XA.Foundation.Search']" />
```

```csharp
public class BucketableIndexResolver : IndexResolver, IIndexResolver
{
    ISearchIndex IIndexResolver.ResolveIndex(Item contextItem)
    {
        // same "indexes" property lookup as the stock resolver, EXCEPT the
        // key includes the context item's own short ID as a third segment:
        //   "{db}/{lang}/{shortId}"  then  "{db}/*/{shortId}"
        // i.e. per-ITEM overrides, not just per-site - contextItem.ID.ToShortID()
        ...
        if (contextItem.IsABucket())
        {
            // prefer the bucket-resolved index over the generic per-database one
            var index = ContentSearchManager.GetIndex((SitecoreIndexableItem)contextItem);
            if (!index.Name.Equals($"sitecore_{contextItem.Database.Name}_index", StringComparison.InvariantCultureIgnoreCase))
                return index;
        }
        return ResolveIndex(contextItem); // explicit-interface method calling
                                           // the inherited public IndexResolver.ResolveIndex -
                                           // the base class's own chain, not infinite recursion
    }
}
```

So there are genuinely **two different `{db}/.../{key}` formats** depending
on which resolver is active - don't conflate them:

| Resolver | Key format | Granularity |
|---|---|---|
| Stock `IndexResolver` (default, no override) | `{db}/{lang}` -> `{db}/*` | per site |
| `BucketableIndexResolver` (if this DI override is applied) | `{db}/{lang}/{shortId}` -> `{db}/*/{shortId}` | per item/bucket |

Check whether a solution has registered a custom `IIndexResolver` (grep
`serviceType=".*IIndexResolver"` across `App_Config`) before assuming which
format applies - the two aren't interchangeable, and only one is active at
a time (`patch:instead` fully replaces the stock registration).

**The database (`{db}` above) isn't part of the search request models at
all** - `QueryModel`/`FacetsModel`/`BaseModel` have no database property, and
`SearchService.GetContextItem` just does `Context.Database.GetItem(itemId)`,
reading whatever `Context.Database` already is for the current request (also
where `contextItem.Database.Name`, the `{db}` in `sitecore_sxa_{db}_index`,
comes from).

That said, `Context.Database` for the request *can* be switched before the
search controller ever runs - by core Sitecore's own `sc_database` query
string switch (`Sitecore.Pipelines.HttpRequest.DatabaseResolver`, part of
the standard `httpRequestBegin` pipeline, not anything SXA/search-specific -
`sc_content` is **not** this key, that's a red herring for a different,
unrelated client/page-state string). It's gated, though:

```csharp
protected virtual bool CanSetDatabaseByQueryString(HttpRequestArgs args, string databaseName)
{
    if (string.IsNullOrEmpty(databaseName)) return false;
    User user = args.SitecoreContext.User;
    if (user != null)
    {
        if (!user.IsAdministrator) return user.IsInRole(Constants.SitecoreClientUsersRole);
        return true;
    }
    return false;
}
```

So `?sc_database=master&...` on a `/sxa/search/results` call **only** takes
effect if the request is authenticated as an Administrator or a member of
`Sitecore Client Users` - for an anonymous front-end visitor it's silently
ignored (`Context.Database` stays whatever the site's configured database
is). Not something a public-facing search widget can rely on; only useful
for an authenticated CM-side/admin request.

**Practical implication for testing `sc_database`:** a plain anonymous call
(browser fetch, unauthenticated `Invoke-WebRequest`) won't carry Sitecore
auth, so `sc_database` gets silently dropped and it looks like the parameter
does nothing. To actually exercise it, issue the request through the
authenticated session from "Logging into a Sitecore instance" in the
`sitecore` skill - reuse its `$webSession` (from `New-SitecoreSession`) via
`Invoke-WebRequest -WebSession $webSession -Uri "$Url/sxa/search/results?...
&sc_database=master"` in PowerShell, not an anonymous request. `sc_site` is
unrelated to this - it isn't gated by authentication at all (see above), so
don't conflate the two: only `sc_database` needs the authenticated session,
because only `sc_database` is permission-checked.

### Filtering by a facet: the query string key is the Facet item's own name

`SearchService.GetQuery` calls `query.ApplyFacetFilters(Context.Request.
QueryString, ...)` (`FacetExtensions.cs`) for **every** request (`GetResults`
and `GetFacets` both), not just `GetFacets` - so a facet filter param on
`/sxa/search/results` narrows the actual results, not only the facet counts.

`ApplyFacetFilters` matches query string keys against Facet items under
`{sxa-site}/Settings/Facets/{facet}` (`FacetService.GetFacetItems`, via
`MultisiteContext.GetSettingsItem(site).FirstChildInheritingFrom(Templates.
FacetsGrouping.ID)`) by the Facet item's **own Sitecore item name** -
`facetItem.Name` - then reads the filter value with `queryString[facetItem.
Name]`. That's the content-tree node name of the Facet item itself, **not**
its `Name` field (`Templates.Facet.Fields.Name` is only used as the
`FriendlyName`/`Facet.Name` label shown in `GetFacets`' aggregation
response - a different value). So to filter by a Facet item named `Category`,
send `?...&Category=SomeValue`, regardless of what that item's `Name` field
is set to.

Value format depends on the Facet's type (checked via `DoesItemInheritFrom`):
- Plain match: exact value, or `|`-separated to build an OR-set (`_empty_`
  represents an empty value)
- Range (`FloatFacet`/`IntegerFacet`/`DateFacet`/generic): `from|to` (either
  side omittable for an open-ended range)
- `DistanceFacet`: a distance string (e.g. `10km`) evaluated against the `g`
  coordinate as the query's center

### Search Scope: the item behind the `s` param

`s` (`ScopesIDs`) takes one or more Sitecore item IDs, `,`/`|`-separated;
each referenced item's `ScopeQuery` field contributes a query clause (OR'd
together across multiple scopes) that narrows what the search actually runs
against - independent of, and in addition to, whatever `itemid`/`sc_site`
already resolve as the index/home-item scope.

Live-verified against `sitecorex41.dev.wsc` (site `SitecoreX/Demo`) by
inspecting its own built-in default scope:

| Fact | Value |
|---|---|
| Template name | `Scope` |
| Template ID | `{8B649372-CC12-4F31-802A-8C3B3D09BB3F}` |
| Location | `{sxa-site}/Settings/Scopes/{scope name}`, e.g. `/sitecore/content/SitecoreX/Demo/Settings/Scopes/Site` |
| Field | `ScopeQuery` - a Sitecore fast-query expression, e.g. the built-in "Site" scope's value was `fast:/sitecore/content/SitecoreX/Demo//*` |

Every SXA site is provisioned with at least one scope (typically named
`Site`, scoping to everything under that site) under `Settings/Scopes` by
default - so unlike Rendering Variants, this folder doesn't usually need to
be created from scratch, only new sibling Scope items added to it.

`Scope` items also carry a Boosting rule set (evaluated by
`IBoostingService.BoostQuery`) - see `SharpPS.Sitecore.ContentSearch.XA`'s
own docs if extending that rule editor is relevant, out of scope here.

Don't assume a new component needs its own scope with a narrowed
`ScopeQuery` - many components are fine reusing the site's existing default
scope (or no `s` param at all). Only create a new Scope item when the
component genuinely needs to search a different subtree/root than the
site default, and leave `ScopeQuery` empty for the author to fill in
deliberately (e.g. in Content Editor) rather than guessing a fast-query
expression for them.

## Response shapes

All three carry `TotalTime`, `QueryTime`, `Signature`, `Index`, plus their own results array.

| Type | Extra fields |
|---|---|
| `ResultSet` | `Count`, `Results: Result[]` |
| `FacetSet` | `Facets: Facet[]` |
| `SuggestionsSet` | `Results: Suggestion[]` |

| Model | Fields |
|---|---|
| `Result` | `Id`, `Language`, `Path`, `Url`, `Name`, `Html` (see `v`/`VariantID` section above) |
| `Facet` | `Key`, `Name`, `DisplayName`, `Values: FacetValue[]` |
| `FacetValue` | `Name`, `Count` |
| `Suggestion` | `Term`, `Payload`, `Html` (mirrors `Term`) |

Geolocation requests (`g` param present) return a `Result` with an extra
`Geospatial` property (distance/coordinate info relative to the request's
`g` center) instead of the plain shape above.

## Suggestions behavior

`GetSuggestions` behavior depends on the `search:define` appSetting: on
Lucene it's just `GetResults` with each result's rendered `Html` returned as
a `Suggestion.Term`; on Solr it calls the native Solr Suggest handler
(`sxaSuggester`, top 5) for real prefix suggestions.

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
- Tenant/Site (same as the `sitecore` skill's CMS section - never assume)
- Variant name
- Whether it's plain field-based (`VariantText`/`VariantField`/etc.) or a
  **Component Variant Field** reusing a Rendering - if the latter, it must be
  a Controller Rendering, not a View Rendering and not a new custom
  controller (see the `sxa-cshtml-controller-rendering` skill for the exact
  fields/why), and check whether that rendering (and its backing
  Feature-layer template/rendering item, per the `sitecore` skill's CMS
  workflow) already exists or needs to be created first
- Whether this needs its own Search Scope (a new `s` value) or can reuse the
  site's existing default scope - don't assume a new scope is needed, see
  "Search Scope" above

**Plan - resolve in dependency order:**
1. If using a Component Variant Field and the rendering doesn't exist yet:
   run the `sitecore` skill's template/rendering/datasource workflow first,
   creating it directly as a Controller Rendering per the
   `sxa-cshtml-controller-rendering` skill - the Component Variant Field's
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
   see "Search Scope" above

**Execution:**
1. Create the `.cshtml` file and register it in the `.csproj` (see below)
2. Create the variant item and its field node(s), and the scope item if
   needed, via `New-SPESession` + `Invoke-RemoteScript` (same mechanism as
   the `sitecore` skill's CMS example - don't just describe the Content
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
`sxa-cshtml-controller-rendering` skill for the full why/how - it covers reusing
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
