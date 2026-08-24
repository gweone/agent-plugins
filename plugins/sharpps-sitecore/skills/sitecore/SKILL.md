---
name: sitecore
description: Use when working on a $solutionpathformat$ Sitecore solution scaffolded from the SharpPS solutionitems template - interacting with a running Sitecore instance (publish, Unicorn sync, site warm-up, migrations) via the SharpPS.Shells PowerShell module.
---

# Sitecore instance interaction (SharpPS.Shells)

## Bootstrap the PowerShell module first

Before running any Sitecore-instance operation, bootstrap the `SharpPS.Shells`
PowerShell module via the solution's `tools/powershell/launcher.ps1`. This
script is what installs/imports the module - don't `Import-Module
SharpPS.Shells` directly without it, since it also registers the PSRepository
the module is published to and trusts the self-signed certs typically needed
to reach a local Sitecore instance over HTTPS.

```powershell
# from the solution root, elevated PowerShell
.\tools\powershell\launcher.ps1
```

What it does:
- Registers the `SharpPSGallery` PSRepository (`https://www.myget.org/F/sharpps/api/v2`) if not already registered
- Trusts self-signed certs (`Set-CertificatePolicy`) so `Invoke-WebRequest`/`Invoke-RestMethod` can reach local HTTPS Sitecore instances
- Installs `SharpPS.Shells` from that repository if `Start-Pipeline` isn't already available on the machine, then `Import-Module SharpPS.Shells`
- Runs the `Install` pipeline for `git`, the Chocolatey Visual Studio extension package, and `dotnet-sdk`

## Where a solution's basic Sitecore info lives

`SharpPS.config` at the **solution root** (not under a physical
`.configuration/` folder - `.configuration` is only the vstemplate's grouping
label; `SolutionItemsWizard.ROOT_PATH` special-cases it so its direct children
land at `$solutiondirectory$` itself, while true child folders like
`.github/` and `.claude/` keep their own path) is the single source of truth
for a solution's basic Sitecore info:

```xml
<configuration>
	<version>$sc_version$</version>
	<demo>$sc_demoversion$</demo>
	<url>$sc_url$</url>
	<nuget>$solutiondirectory$\nuget</nuget>
	<dbprovider>$sc_db_provider$</dbprovider>
	<dbpackage>$sc_db_package$</dbpackage>
	<dbpackageversion>$sc_db_package_version$</dbpackageversion>
	<framework>$targetframeworkversion$</framework>
	<area>$mvc_area$</area>
	<publishpath>$sc_publishpath$</publishpath>
	<core>$solutionpathformat$</core>
	<repository>$sc_git_repository$</repository>
	<branch>$sc_git_branch$</branch>
</configuration>
```

- `url` is the Sitecore instance base URL - the same value to pass as `-Url`
  to `New-SitecoreSession`, `Invoke-SitecorePublish`, `Invoke-SyncUnicorn`,
  `Start-SiteUp`, etc.
- `publishpath` is the IIS site's webroot the solution builds/publishes to.
- The VS project wizards (`SitecoreProjectWizard`, `SitecoreItemWizard`)
  look up this file at the solution root on every "Add New Project" and read
  it back to auto-fill the same `$sc_*$` template parameters, so these values
  only need to be entered once per solution (in the wizard UI, when the file
  doesn't exist yet) rather than on every new Feature/Foundation project. If
  it's missing, the wizard falls back to a `SharpPSConfiguration` environment
  variable, then to prompting via UI.
- It's marked `Exclude="true"` in `solutionitems.vstemplate`, so it's written
  to disk but not shown as a visible Solution Explorer node.

### Pipelines resolve it by default - no need to pass -Args

`Register-Pipeline` sorts each pipeline folder's scripts alphabetically
(`Directory.GetFiles(pipeline).OrderBy(x => x)` in
`RegisterPipelineCmdletCommand.cs`), so a `00-*` file always runs first for
that pipeline. The `Sitecore`, `Publish`, and `Artifact` pipelines each start
with a `00-Resolve-SharpPS.ps1` step that reads `sharpps.config` from the
**current directory** (not the parameterized solution path - `Start-Pipeline`
must be invoked from the solution root) and, for any key not already present
in `-Args`, fills in:
- `Url`, `PublishUrl`, `Core`, `SolutionPath` (all three pipelines)
- `SitecoreUsername` (default `"admin"`), `SitecorePassword` (default `"b"`) - Sitecore pipeline only

Because `$Args` is a `Hashtable` passed by reference through every subsequent
step, these resolved values are visible for the rest of the pipeline run.
This means calls like `Start-Pipeline -Name Sitecore` or `Start-Pipeline
-Name Publish` don't need `-Args` at all when run from a solution root that
has `sharpps.config` - only pass `-Args` to override a specific value.
`Install`, `Startup`, `SIF`, and `Traefik` pipelines do **not** have this
step and don't auto-resolve from `sharpps.config`.

## Logging into a Sitecore instance

Any authenticated interaction with the instance (publish, admin pages, etc.)
goes through `New-SitecoreSession` first - it's the cmdlet the module uses
under the hood to authenticate. It logs into `$Url/sitecore/login`, scrapes
the login form (`Get-HtmlInputs`), submits the credentials, and returns a
`WebRequestSession` object to reuse in subsequent `Invoke-WebRequest` calls
via `-WebSession`.

```powershell
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$webSession = New-SitecoreSession -Url $Url -Username $Username -Password $securePassword

Invoke-WebRequest -Uri "$Url/sitecore/admin/dbbrowser.aspx" -WebSession $webSession -Method Post -Body @{ ... }
```

- `-Url` - Sitecore instance base URL, e.g. `https://mysite.dev.local`
- `-Username` / `-Password` (`SecureString`) - Sitecore admin credentials; functions built on top of this (`Invoke-SitecorePublish`, `Get-UnicornAutoPublish`) default `Username` to `admin` and `Password` to `b` when not overridden
- Calls `Set-TrustPolicy` internally, so self-signed local certs don't need to be trusted separately first
- Writes an error and returns nothing if the login form can't be parsed or the credentials are rejected - check for a `null`/empty session before reusing it

## Reading the live merged configuration

The fully patched/merged runtime `Sitecore.config` (every `App_Config\Include`
patch applied) is available at `/sitecore/admin/showconfig.aspx` - it needs
an authenticated session, i.e. the `$webSession` from `New-SitecoreSession`:

```powershell
$webSession = New-SitecoreSession -Url $Url -Username $Username -Password $securePassword
$config = Invoke-WebRequest -Uri "$Url/sitecore/admin/showconfig.aspx" -WebSession $webSession -UseBasicParsing
```

Use this to verify a config patch actually made it into the merged result
instead of assuming from the source `.config` file on disk - e.g.
`Get-UnicornAutoPublish` fetches this page and regex-matches for
`TriggerAutoPublishSyncedItems` to confirm `Unicorn.AutoPublish.config`'s
patch is live, since that's what actually drives auto-publish after a
Unicorn sync (a plain `Publisher().Publish()` call, like `dbbrowser.aspx`
triggers, does not pick up Unicorn-synced items on its own).

## CMS content-tree conventions (templates, renderings, datasources)

### Workflow: Spec -> Plan -> Execution

**Spec - ask the user if any of this is missing, don't guess:**
- Tenant (`{site-folder}`) and Site (`{sxa-site}`) - never assume there's
  only one
- Feature name and Rendering name the template/rendering/datasource belong to
- Sitecore credentials, if the `admin`/`b` default turns out not to work
- Confirm SPE Remoting is reachable (`New-SPESession` succeeds) before
  planning further - if it fails outright (not a credentials problem), that's
  a `Register-SPE` prerequisite issue, not something to work around

**Plan - resolve every path before creating anything, in this order (later
items depend on earlier ones existing):**
1. Datasource template path (`/sitecore/templates/Feature/{core}/{area}/
   {featurename}/*`) - fields matching what the rendering's code
   actually reads
2. Rendering path (`/sitecore/layout/Renderings/Feature/{core}/{area}/
   {featurename}/*`) - references the template from step 1 as its
   `Datasource Template`
3. Datasource item path (`{sxa-site}/Data/{core}/{area}/{featurename}/
   {renderingname}/*`) - built from the template in step 1

**Execution:** run all three through one `New-SPESession` +
`Invoke-RemoteScript` call (example below) rather than three separate
sessions, and set the rendering's `Datasource Template`/`Datasource
Location` fields to the results of steps 1/3 afterward so Content Editor's
datasource picker offers them.

| Item type | Path |
|---|---|
| SXA site | `/sitecore/content/{site-folder}/{sxa-site}` |
| Site data (rendering datasource items) | `{sxa-site}/Data/{core}/{area}/{featurename}/{renderingname}/*` |
| Rendering | `/sitecore/layout/Renderings/Feature/{core}/{area}/{featurename}/*` |
| Datasource template | `/sitecore/templates/Feature/{core}/{area}/{featurename}/{renderingname}` |

`{core}` is `SharpPS.config`'s `core` value (`$solutionpathformat$`) and
`{area}` is its `area` value (`$mvc_area$`, default `v1`) - the same tokens
used throughout this solution's config/rendering paths (see "Where a
solution's basic Sitecore info lives" above). `{site-folder}` (the Tenant)
and `{sxa-site}` are **not** derivable from `SharpPS.config` or anything else
in the repo - there can be multiple tenants/sites per instance. **Ask the
user which Tenant/Site to target before constructing any of these paths or
creating items** - don't guess a name or assume there's only one.

- Every rendering that takes a datasource needs a matching template under
  the Datasource template path above **first** - build the template's fields
  to match whatever the rendering's code actually reads (view model /
  controller), not the other way around.
- Template, rendering, and datasource items can all be created directly
  through a Sitecore session instead of manually through Content Editor -
  actually run the creation via the SPE session below rather than just
  describing the manual Content Editor steps and stopping there:
  - `New-SitecoreSession` (see above) only gets you an authenticated
    `WebRequestSession` for HTTP calls to existing admin pages - it can't
    create items on its own.
  - `New-SPESession` (wraps Sitecore PowerShell Extensions' Remoting module -
    `Import-Module SPE; New-ScriptSession -Username ... -Password ...
    -ConnectionUri $Url`) opens a **remote PowerShell session** into the
    instance, letting you run arbitrary Sitecore PowerShell (`New-Item`,
    etc.) against the content tree remotely. Defaults to
    `sitecore\admin`/`b` if `-Username`/`-Password` aren't passed.
  - **`-Password` here is a plain `[string]`, not a `SecureString`** -
    unlike `New-SitecoreSession` above (whose `-Password` *is* a
    `SecureString`, requiring `ConvertTo-SecureString` first). Pass the
    plain password directly to `New-SPESession -Password $Password`; don't
    reuse a `ConvertTo-SecureString`'d value from the `New-SitecoreSession`
    flow - a `SecureString` bound to a `[string]` parameter stringifies to
    `System.Security.SecureString`, so the remoting endpoint receives that
    literal text instead of the password and authentication fails silently
    with no obviously-related error.
  - If the default credentials fail (e.g. the instance's admin password was
    changed), ask the user for the actual credentials rather than retrying
    the default or giving up on item creation entirely.
  - SPE Remoting must already be installed and enabled on the target
    instance for `New-SPESession` to work - `Register-SPE -SitecorePath
    <webroot>` installs the SPE Minimal + Remoting packages and flips the
    `remoting`/`fileDownload` services in `App_Config\Include\Spe\spe.config`
    to `enabled="true"` if they aren't already. Enabling `<remoting>` alone
    is **not** enough to connect, though - its `<authorization>` only allows
    the `sitecore\PowerShell Extensions Remoting` role by default, so
    `Register-SPE` also adds an explicit `<add Permission="Allow"
    IdentityType="Role" Identity="sitecore\IsAdministrator" />` entry so any
    administrator account (including the default `sitecore\admin`) can
    connect, without needing to know or pass a specific username up front.

**Reference syntax for SPE cmdlets:** the official Sitecore PowerShell
Extensions documentation (https://doc.sitecorepowershell.com) is the
source of truth for exact cmdlet parameters (e.g. `New-Item`,
`Add-ItemTemplateSection`, `Add-ItemTemplateField`, field-sharing switches)
- confirm against it (or `Get-Help <cmdlet> -Full` on the target instance)
before relying on a remembered signature, rather than guessing. The
"Working with Items" page (https://doc.sitecorepowershell.com/working-with-items)
covers item creation/editing patterns specifically - the closest match to
the `New-Item`/`Editing.BeginEdit()`/`Editing.EndEdit()` mechanics used
throughout this skill.

### Example: creating a template, rendering, and datasource item

Run everything against the remote session via SPE Remoting's
`Invoke-RemoteScript` - the script block executes on the Sitecore instance,
not locally. `$SxaSiteCollection`/`$SxaSite` are the Tenant/Site the user gave you -
pass them in explicitly, don't leave them to resolve from an outer scope:

```powershell
$speSession = New-SPESession -Url $Url -Username $Username -Password $Password

Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($core, $area, $featureName, $renderingName, $sxaSiteCollection, $sxaSite)

    $templateFolder = "master:/sitecore/templates/Feature/$core/$area/$featureName"
    $template = New-Item -Path $templateFolder -Name $renderingName -ItemType "/sitecore/templates/System/Templates/Template"
    Add-ItemTemplateSection -Item $template -Name "Data"
    Add-ItemTemplateField -Item $template -Section "Data" -Name "Title" -Type "Single-Line Text"

    $renderingFolder = "master:/sitecore/layout/Renderings/Feature/$core/$area/$featureName"
    New-Item -Path $renderingFolder -Name $renderingName -ItemType "/sitecore/templates/System/Layout/Renderings/View Rendering"

    $dataFolder = "master:/sitecore/content/$sxaSiteCollection/$sxaSite/Data/$core/$area/$featureName/$renderingName"
    New-Item -Path $dataFolder -Name "Sample $renderingName" -ItemType $template.ID
} -ArgumentList $Core, $Area, $FeatureName, $RenderingName, $SxaSiteCollection, $SxaSite
```

Set the new rendering item's `Datasource Template`/`Datasource Location`
fields to point at the template and data folder created above so Content
Editor's "Insert options" and datasource picker offer them automatically.

### Serializing an item to disk - `Export-Item`, not Unicorn

To write a Sitecore item (e.g. one just created above) to disk as a file,
use SPE's own built-in `Export-Item` cmdlet
(`Spe.Commands.Serialization.ExportItemCommand`) inside the same
`Invoke-RemoteScript` session - this is **not** Unicorn (a separate module
this solution doesn't necessarily have installed) and has nothing to do with
`Invoke-SyncUnicorn`/`Sync-Unicorn`. It serializes to Sitecore's classic
`.item` format via `Sitecore.Data.Serialization.Manager.DumpItem`:

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($itemPath)
    Get-Item -Path $itemPath | Export-Item -Recurse
} -ArgumentList "master:/sitecore/templates/Feature/$core/$area/$featureName/$renderingName"
```

- `-Recurse` also serializes the item's children (e.g. a template's field items)
- `-Root`/`-Target` (alias) sets the output folder explicitly; if omitted, it
  defaults to Sitecore's own serialization path
  (`App_Data\serialization\{database}\...`) - **on the Sitecore instance's
  filesystem**, since the script block runs server-side through
  `Invoke-RemoteScript`, not on whatever machine started the SPE session. If
  the target repo's source tree needs the serialized file (not just the
  server's `App_Data`), pass `-Root` pointing at wherever that's mounted/
  reachable from the server, or retrieve the file afterward - it does not
  land in the local working directory on its own.

## Cmdlets available once imported

- `Start-Pipeline -Name Sitecore` - deploy the Sitecore solution
- `Start-Pipeline -Name Publish -Args @{ PublishUrl = "C:\Custom\Path" }` - publish to a specific path
- `Invoke-Migration` - run database migration
- `Invoke-SyncUnicorn -Url "https://cm.sitecore.dev"` - sync Unicorn serialization
- `Start-SiteUp -Url "https://cm.sitecore.dev"` - warm up the site
