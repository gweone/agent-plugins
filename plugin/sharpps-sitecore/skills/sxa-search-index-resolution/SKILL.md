---
name: sxa-search-index-resolution
description: Use to diagnose which index or database native Sitecore SXA search queries, including itemid, sc_site, sc_database authentication, site indexes mappings, IIndexResolver overrides, and fallback resolution.
---

# SXA search index resolution

Use this skill when the search endpoint queries the wrong index/database,
or when configuring the stock or an existing custom `IIndexResolver`.
No broad Sitecore skill is a prerequisite.

## Lookup

- [Site and database request example](references/index-resolution.md#how-to-specify-site-and-database-on-a-search-request)
  — authenticated PowerShell request and live observations.
- [Stock resolver and fallback chain](references/index-resolution.md#no-way-to-specify-the-index-name-directly---its-always-server-resolved)
  — site `indexes` mappings, database/language keys, page-mode defaults.
- [Core fallback pipeline](references/index-resolution.md#the-real-last-resort-mechanism-core-sitecores-contentsearchgetcontextindex-pipeline)
  — database-root lookup, crawlers, ranking, and excluded indexes.
- [When sc_site matters](references/index-resolution.md#how-sc_site-actually-reaches-this-and-usually-doesnt)
  — overlapping content roots, not primary site/index selection.
- [Per-item/bucket override and database gate](references/index-resolution.md#going-beyond-site-level-overriding-iindexresolver-for-per-itembucket-resolution)
  — existing `BucketableIndexResolver` example, DI registration, and
  `CanSetDatabaseByQueryString` implementation.

## Diagnostic and safety checklist

1. Capture `itemid`, the returned `Index`, request site, page mode, and
   authentication context. An unresolved/missing item skips item-specific
   resolution and goes directly to page-mode defaults.
2. Inspect active `IIndexResolver` registration before choosing key formats:
   stock `{db}/{lang}` differs from custom `{db}/{lang}/{shortId}`.
3. Follow the existing fallback chain; do not invent an `?index=` override.
4. Do not equate public `sc_site` with database selection. It scopes the
   home item and only disambiguates index sites with overlapping roots.
5. `sc_database` is core Sitecore behavior, not an SXA model property.
   It only works for an authenticated Administrator or member of
   `Sitecore Client Users`; anonymous requests silently ignore it.
6. For authorized CM/admin testing, reuse an authenticated `$webSession`
   with `Invoke-WebRequest -WebSession`; do not rely on `sc_database` in
   public-facing widgets. `sc_content` is not the database switch.
7. If a custom resolver is needed, preserve stock fallback behavior by
   inheriting `IndexResolver`, as shown in the reference.

## Related skills

- [sxa-search](../sxa-search/SKILL.md) — routes, query parameters, scopes/facets.
- [sxa-search-result-variants](../sxa-search-result-variants/SKILL.md)
  — result `Html` and the `v` parameter.
- [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md)
  — authenticated sessions for the database-switch test.
- [sitecore-template-items](../sitecore-template-items/SKILL.md)
  — supporting Sitecore item work.
