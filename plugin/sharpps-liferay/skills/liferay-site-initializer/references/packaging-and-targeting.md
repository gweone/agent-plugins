# Packaging and ERC targeting

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Two implementation forms — prefer the Client Extension form on 7.4+/Quarterly

| Form | Where | When |
|---|---|---|
| **Client Extension** (`type: siteInitializer`) | `client-extensions/<name>/client-extension.yaml` + `client-extensions/<name>/site-initializer/...` | **Default choice on 7.4+/Quarterly Release workspaces** (as preferred in the original consuming workspace's `CLAUDE.md` (external precedent)). No custom Java or separate application build — the workspace plugin auto-zips and deploys it. |
| **OSGi module** implementing `SiteInitializer` | A module with `Liferay-Site-Initializer-*` `bnd.bnd` headers, resources under `src/main/resources/site-initializer/` | Only when you need custom Java logic the declarative form can't express. Both forms are read by the **same engine** (`BundleSiteInitializer`), so the resource-folder contract below is identical either way. |

Both forms are processed by
`modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/.../internal/BundleSiteInitializer.java`
in `liferay-portal` — **this file is the single source of truth**. It may be ahead of the
release this workspace runs on, so when in doubt, grep it rather than trust this skill's tables
blindly ([token and source verification](tokens-and-source-verification.md) has the exact greps).

## Minimal `client-extension.yaml`

```yaml
my-site-initializer:
    name: My Site Initializer
    oAuthApplicationHeadlessServer: my-site-initializer-oahs
    siteExternalReferenceCode: MY_SITE
    siteName: My Site
    type: siteInitializer
my-site-initializer-oahs:
    .serviceAddress: localhost:8080
    .serviceScheme: http
    name: My Site Initializer OAuth Application Headless Server
    scopes:
        -   Liferay.Headless.Site.everything
    type: oAuthApplicationHeadlessServer
```

`Liferay.Headless.Site.everything` alone is what Liferay's own official samples use even when
the initializer also imports objects/documents/web content/blueprints (`liferay-sample`,
`liferay-learn`, `liferay-partner-site-initializer-code` in
`liferay-portal/workspaces/*/client-extensions/`) — the engine calls the internal REST resources
in-process as the current user, not via this OAuth app, so extra scopes are normally only needed
if something *else* will call this CX's headless APIs later. Don't copy a huge scope list from a
real-world sample without checking whether your initializer actually needs it.

### `siteExternalReferenceCode` semantics — confirmed by tracing `SiteResourceImpl.putSiteSiteInitializer`

This property is the actual **targeting key**, not just a label for a brand-new site:

- On every deploy, `SiteInitializerClientExtension` (a `BundleTrackerCustomizer`) looks up a Group
  by this ERC. **Found → updates that existing site in place** (re-running upserts everything by
  ERC, doesn't duplicate). **Not found → creates a new site**, using `siteName` as its name.
- This is fully automatic — there is no separate "pick an initializer" UI step for the
  `client-extension.yaml` form; it runs the instant the bundle activates.
- **Never point this at a system-required site** (`L_GUEST`, Global, Control Panel) — see
  [system-site prohibition](limitations.md#system-required-sites). New sites and ordinary existing (non-system) sites both work fine.

## What `type: siteInitializer` actually builds — and why most of it doesn't matter here

Building this CX produces (under `client-extensions/<name>/build/liferay-client-extension-build/`):

```
Dockerfile                                  # FROM liferay/batch:latest — LXC/Cloud packaging
LCP.json                                    # "kind": "Job", LXC orchestration metadata
<name>.client-extension-config.json         # OAuth2 app config (real, gets applied)
site-initializer/site-initializer.json      # {"externalReferenceCode", "name"} from the yaml
site-initializer/site-initializer.zip       # the REAL OSGi-deployable artifact
```

**The `Dockerfile`/`LCP.json` are for Liferay Cloud (LXC)'s build pipeline and are irrelevant on
a self-hosted/plain-Docker instance** (no LXC control plane = nothing ever builds or runs that
image). Don't mistake their presence for "this needs a separate batch container" — on a vanilla
`liferay/dxp` Docker container, the *nested* `site-initializer/site-initializer.zip` inside the
outer CX zip is what actually gets picked up by `AutoDeployScanner`/Felix FileInstall and
processed by the same `BundleSiteInitializer` engine as the OSGi-module form. Confirmed by reading
`docker exec liferay-dev` OSGi console output (`lb <name>` shows the bundle `Active`) and matching
log lines (`BundleSiteInitializer:536 Initializing <site> for group <id>`) after a plain
`cp dist/<name>.zip /path/to/deploy/`.
