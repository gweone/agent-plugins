# SXA search index and database resolution

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
  no authentication needed. Drives home-item/predicate scoping
  (`PageOrMediaPredicate`) - **not** the same thing as choosing a
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

`QueryModel`/`FacetsModel`/`BaseModel` (see the [parameter table](../../sxa-search/references/api-and-query.md#query-string-parameters)) have no
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
authenticated session from [sitecore-spe-remoting](../../sitecore-spe-remoting/SKILL.md) —
reuse its `$webSession` (from `New-SitecoreSession`) via
`Invoke-WebRequest -WebSession $webSession -Uri "$Url/sxa/search/results?...
&sc_database=master"` in PowerShell, not an anonymous request. `sc_site` is
unrelated to this - it isn't gated by authentication at all (see above), so
don't conflate the two: only `sc_database` needs the authenticated session,
because only `sc_database` is permission-checked.

