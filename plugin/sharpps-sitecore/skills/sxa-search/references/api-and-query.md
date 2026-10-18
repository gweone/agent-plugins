# SXA native search API, scopes, and facets

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
| `Result` | `Id`, `Language`, `Path`, `Url`, `Name`, `Html` (see [result variants](../../sxa-search-result-variants/SKILL.md)) |
| `Facet` | `Key`, `Name`, `DisplayName`, `Values: FacetValue[]` |
| `FacetValue` | `Name`, `Count` |
| `Suggestion` | `Term`, `Payload`, `Html` (mirrors `Term`) |

Geolocation requests (`g` param present) return a `Result` with an extra
`Geospatial` property (distance/coordinate info relative to the request's
`g` center) instead of the plain shape above.

## Suggestions behavior

### Prerequisite: configured Solr suggester

The [SXA 10.4 search-service documentation](https://doc.sitecore.com/xp/en/developers/sxa/104/sitecore-experience-accelerator/the-sxa-search-service.html)
states that Search Box predictions are available only with the Solr search
provider using `sxaSuggester`. For the standard Search Box rendering, set
**Suggestions mode → Show predictions** in its Control Properties.
Enabling the UI or calling `/sxa/search/suggestions` does not configure Solr.

Before choosing that endpoint, verify the actual resolved search index/core
has the appropriate Solr suggest component/request handler, the
`sxaSuggester` dictionary, a suitable source field, and a built dictionary.
Use the target release's configuration and the
[Solr auto-suggest documentation](https://doc.sitecore.com/xp/en/developers/104/platform-administration-and-architecture/en/using-solr-auto-suggest.html);
its generic example is not a ready-made SXA configuration. Building or
rebuilding dictionaries, editing Solr configuration, and reloading cores
require separate authorization; do not perform them just to implement a UI.

The previously inspected implementation selects behavior through the
`search:define` appSetting: its Solr branch calls the native Solr Suggest
handler (`sxaSuggester`, top 5); its historical Lucene branch maps rendered
result `Html` into `Suggestion.Term`. This is implementation evidence, not
proof that Lucene predictions are supported in SXA 10.4.

The shared model-binding table above is not a guarantee that the Solr
suggestion branch honors every results parameter. The SXA 10.4 documentation
lists `q`, `v`, `p`, and `itemid` for suggestions, with a default `p` of 5;
verify actual behavior rather than assuming result scopes/facets, ordering,
offsets, or variants affect a native suggestion dictionary identically.

### Fallback: use search results as UI suggestions

If `sxaSuggester` is not configured or verified, use
`/sxa/search/results` for a custom result-based autocomplete dropdown instead
of relying on `/sxa/search/suggestions` or silently changing Solr setup.
This fallback is custom client behavior, not a built-in automatic fallback
for the standard SXA Search Box's **Show predictions** mode.

- Send the typed text as URL-encoded `q` and an explicit small `p` (for
  example, 5). Preserve the intended `sc_site`, `itemid`, language, existing
  scope `s`, and applicable facet filters, just as for the full search page.
- Map `Results[].Name` and `Results[].Url` to clickable suggestions. If custom
  result markup is needed, use a verified rendering variant through `v` and
  inspect `Results[].Html`; it is not a `Suggestion.Term` response.
- Debounce requests, use a minimum input length, and ignore stale responses.
  Escape text labels and validate navigation URLs; do not treat indexed text
  as trusted HTML.
- This returns matching content items, not dictionary-based term predictions.
  Prefix matching, spelling correction, and prediction ranking are not
  guaranteed by switching endpoints; they depend on the actual search query
  and index configuration. Handle empty results and failures explicitly.

