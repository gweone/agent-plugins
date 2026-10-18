---
name: sxa-search
description: Use for native Sitecore SXA /sxa/search/results, /facets, and /suggestions API routes, query parameters, response shapes, Search Scope items, and facet filtering.
---

# SXA native search API

Use this skill for `Sitecore.XA.Feature.Search.Controllers.SearchController`,
a Web API controller: query string input, JSON output.
Read the relevant reference section directly; no broad Sitecore skill is required.

## Lookup

- [Routes and query parameters](references/api-and-query.md#query-string-parameters)
  — `q`, `s`, `l`, `sig`, `sc_site`, `itemid`, `g`, `o`, `e`, `p`, `v`, `f`.
- [Facet filtering](references/api-and-query.md#filtering-by-a-facet-the-query-string-key-is-the-facet-items-own-name)
  — item-name keys, match/OR, range, and distance values.
- [Search Scope items](references/api-and-query.md#search-scope-the-item-behind-the-s-param)
  — template ID, location, `ScopeQuery`, and when not to create a scope.
- [Response shapes](references/api-and-query.md#response-shapes)
  — results, facets, suggestions, and geolocation output.
- [Suggestions prerequisites and fallback](references/api-and-query.md#suggestions-behavior)
  — Solr `sxaSuggester` setup; otherwise use results for custom autocomplete.

## Request checklist

1. Choose `/sxa/search/results`, `/sxa/search/facets`, or
   `/sxa/search/suggestions`; account for the site's virtual folder.
2. Resolve the intended site/context item; do not confuse `sc_site` with
   choosing a database or an index.
3. Reuse an existing Search Scope when suitable. Create a new one only for
   a deliberately different search root; leave `ScopeQuery` for the author
   rather than guessing a fast-query expression.
4. Filter using the Facet item's own item name, not its `Name` field.
   Facet filters also narrow `/results`, not just facet counts.
5. For rendered `Html`, pass a Rendering Variant definition ID as `v`.
6. Use `/suggestions` only after verifying Solr `sxaSuggester` configuration
   and its built dictionary. Otherwise use `/results` with a small `p` for
   custom result-based autocomplete; it returns items, not term predictions.
   Do not automatically configure or rebuild Solr to enable suggestions.
7. Check the returned `Index` and result shape when diagnosing a request.
   The presence of `g` alone selects geolocation mode.

## Related skills

- [sxa-search-index-resolution](../sxa-search-index-resolution/SKILL.md)
  — index fallback chain, `sc_site`, and authenticated `sc_database` tests.
- [sxa-search-result-variants](../sxa-search-result-variants/SKILL.md)
  — `v`, result markup, Component Variant Fields, and variant selectors.
- [sxa-cshtml-controller-rendering](../sxa-cshtml-controller-rendering/SKILL.md)
  — reliable `.cshtml` rendering outside a normal MVC page request.
- [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md)
  — authenticated Sitecore/SPE sessions and remote execution.
- [sitecore-template-items](../sitecore-template-items/SKILL.md)
  — creating the supporting Sitecore items.
