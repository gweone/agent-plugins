# Batch packaging and Guest-site rationale

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Why this exists alongside the Site Initializer skill — the Guest-site workaround

The [initializer system-site prohibition](../../liferay-site-initializer/references/limitations.md#system-required-sites) documents that `siteExternalReferenceCode:
L_GUEST` is permanently blocked: `SiteResourceImpl.putSiteSiteInitializer` →
`GroupLocalServiceImpl.updateGroup` throws `RequiredGroupException$MustNotDeleteSystemGroup`
because that whole code path tries to update the **Group entity itself** (rename/recreate),
which Liferay refuses for the Guest/Global/Control Panel system groups — there is no fix.

A Batch Client Extension sidesteps this entirely: it calls the **same REST resources** (Object
Entries, etc.) the site initializer engine calls internally, but via the generic Headless Batch
Engine, which **never touches the Group entity** — it only looks up the target group's ID to
scope a REST request, the identical lookup ordinary headless API calls already use. Confirmed by
reading `VulcanBatchEngineTaskItemDelegateAdaptor._applyParamConverters` ([site targeting](site-targeting-and-format.md)) — there is no
`updateGroup` call anywhere in this path.

**Practical implication:** Batch Client Extensions are the right tool when you specifically need
to push data into Guest (or Global/Control Panel) and a Site Initializer is blocked. For an
*ordinary* site (new or existing, non-system), prefer the Site Initializer — it covers far more
resource types (pages, documents, web content, KB articles, blueprints) with declarative file
formats matched to each type, whereas Batch's *proven* scope is narrower ([resource evidence](resource-support.md)).

## Minimal `client-extension.yaml`

```yaml
assemble:
    -   from: batch
        into: batch
my-batch:
    name: My Batch
    oAuthApplicationHeadlessServer: my-batch-oahs
    type: batch
my-batch-oahs:
    .serviceAddress: localhost:8080
    .serviceScheme: http
    name: My Batch OAuth Application Headless Server
    scopes:
        -   Liferay.Headless.Batch.Engine.everything
        -   Liferay.Object.Admin.REST.everything
    type: oAuthApplicationHeadlessServer
```

**The `assemble:` block at the top is mandatory and easy to miss — there is no build-time
warning if you omit it.** Confirmed by reproducing the failure end-to-end: without it, the
build still succeeds, `createClientExtensionConfig` still writes
`Liferay-Client-Extension-Batch=batch/` into `WEB-INF/liferay-plugin-package.properties`, but
the **`batch/` folder itself never gets copied into the final dist zip** (verified with
`unzip -l dist/<name>.zip` — only `WEB-INF/`, `Dockerfile`, `LCP.json`, and the CX config JSON
were present, no `batch/`). The deployed bundle's actual manifest then has **no**
`Liferay-Client-Extension-Batch` header at all (verified via `headers <bundleId>` in the OSGi
console) — so `BatchEngineBundleTracker.addingBundle()` returns immediately at its very first
check and does nothing. The result: the bundle installs and goes `Active`, **zero errors or
warnings appear anywhere**, and the import simply never happens. The only way to notice is
`unzip -l` on your own dist zip before deploying, or checking the live bundle's headers after.
Unlike `siteInitializer` (whose `site-initializer/` folder is packaged automatically, confirmed
by its build log showing a dedicated `buildSiteInitializerZip` task), `type: batch` has no
equivalent automatic task — the build log will show `assembleClientExtension NO-SOURCE` and
nothing else copies `batch/` for you.

Confirmed via `client-extension.schema.json` (`gradle-plugins-workspace`): `type: batch` only
requires `oAuthApplicationHeadlessServer` — there is **no `siteExternalReferenceCode`/`siteName`
equivalent at the CX-config level** (unlike `siteInitializer`). The target site is specified
**per batch-engine-data.json file**, via a `parameters` key — see [batch file format](site-targeting-and-format.md#batch-engine-datajson-format).

Add OAuth scopes matching whatever resource types you import — `Liferay.Object.Admin.REST.everything`
for Objects, `Liferay.Headless.Admin.Workflow.everything` for workflows, `Liferay.Headless.Admin.User.everything`
for users/roles, etc. (matches the original consuming project's `.claude/rules/cx.md` guidance (external precedent) for batch-type CX scopes.)
