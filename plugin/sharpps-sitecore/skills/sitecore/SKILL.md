---
name: sitecore
description: Use when working on a $solutionpathformat$ Sitecore solution scaffolded from the SharpPS solutionitems template - interacting with a running Sitecore instance (publish, Unicorn sync, site warm-up, migrations, template/rendering/datasource creation via SPE Remoting) via the SharpPS.Shells PowerShell module. Covers module installation without admin rights, the self-signed-cert trust gotcha for New-SPESession, the correct low-level way to create Template/Template Section/Template Field items via Add-BaseTemplate (Add-ItemTemplateSection/Add-ItemTemplateField are not real cmdlets), serializing newly-created items via Unicorn's own Export-UnicornItem (not SPE's plain Export-Item), retrieving files from a remote instance via Receive-RemoteItem, and running this from Claude Code specifically (the auto mode classifier blocks live SPE writes by default; getting past that needs an explicit, user-approved permission entry).
---

# Sitecore instance interaction (SharpPS.Shells)

## Running this from Claude Code specifically

Claude Code's auto mode classifier treats `New-SPESession`/
`Invoke-RemoteScript` calls that create or modify items on a real instance
as a high-risk write action and blocks them by default - confirmed live on
both the PowerShell tool and the Bash tool (invoking `powershell.exe`
directly), independent of which one is tried. A pure read/connectivity
check (e.g. one `Get-Item` inside `Invoke-RemoteScript`) was not blocked
the same way; the block is specifically about live writes to a remote or
shared instance, consistent with how the harness treats any other
consequential write to shared infrastructure.

Getting past this for a session that genuinely needs to create items live
requires an explicit project permission entry, and that's a decision for
the user to make and ask for - don't add it on your own initiative before
they've said they want live SPE execution to proceed. If they do ask,
project settings documentation covers where such an entry belongs; a
project-local, gitignored settings file (not the shared/committed one) is
the appropriate place for something this specific to one developer's
instance and default credentials. After it's added, a fresh settings load
may be needed before the harness honors it - if the very next attempt is
still blocked, that's the likely reason, not a sign the entry is wrong.

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

**Without admin rights, don't run `launcher.ps1` as-is** - its
`Install-Module SharpPS.Shells ... -Scope AllUsers` line hard-fails
(`AdminPrivilegeRequiredForAllUsersScope`) on a non-elevated shell, live-
confirmed. Replicate its steps manually with `-Scope CurrentUser` instead of
running the script verbatim:

```powershell
$Repository = "SharpPSGallery"
if (-not (Get-PSRepository -Name $Repository -ErrorAction SilentlyContinue)) {
    Register-PSRepository -Name $Repository -SourceLocation "https://www.myget.org/F/sharpps/api/v2" -InstallationPolicy Trusted
}
[Net.ServicePointManager]::SecurityProtocol = "Tls, Tls11, Tls12, Ssl3"
Install-Module SharpPS.Shells -Repository $Repository -Force -Confirm:$false -Scope CurrentUser
Import-Module SharpPS.Shells
```

**`New-SPESession` also needs the separate `SPE` module** (Sitecore
PowerShell Extensions' own Remoting *client* module, `New-ScriptSession`'s
home) - `SharpPS.Shells` calls into it but does not install it, so a fresh
machine needs it pulled from PSGallery too (`SPE`, not `SharpPS.Shells` -
confirmed live as two separate packages):

```powershell
Install-Module SPE -Repository PSGallery -Force -Confirm:$false -Scope CurrentUser -AllowClobber
Import-Module SPE
```

Without this, `New-SPESession` fails with `Import-Module : The specified
module 'SPE' was not loaded` and `New-ScriptSession` not recognized - easy
to misread as an SPE Remoting *server*-side problem when it's actually a
missing *client*-side module.

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

**`New-SPESession` does *not* call `Set-TrustPolicy` for you** - unlike
`New-SitecoreSession` above, connecting via `New-SPESession` against a
self-signed HTTPS endpoint needs the cert-trust override applied explicitly
first (the same `ICertificatePolicy` override `launcher.ps1`'s
`Set-CertificatePolicy` sets up):

```powershell
Add-Type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) { return true; }
}
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
[Net.ServicePointManager]::SecurityProtocol = "Tls, Tls11, Tls12, Ssl3"
```

**This has to be set in the *same* PowerShell process as `New-SPESession`
and every `Invoke-RemoteScript` call that follows it** - `ServicePointManager`
state doesn't persist across separate process invocations. Concretely, this
bit two things live: (1) an agent/automation tool that runs each PowerShell
command as its own fresh process must set the policy, connect, *and* run
`Invoke-RemoteScript` all inside one script/one invocation, not across
several separate tool calls sharing "the same session" only by variable name;
(2) `ServerCertificateValidationCallback = { $true }` (the modern .NET
equivalent) fails differently and unhelpfully in this context - `There is
no Runspace available to run scripts in this thread` - because the callback
runs on a thread with no PowerShell runspace attached. Use the classic
`ICertificatePolicy` override above, not the callback, for this specific
combination.

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

**`Add-ItemTemplateSection`/`Add-ItemTemplateField` do not exist** - live-
verified against a real SPE Remoting session (`Get-Command
Add-ItemTemplateField`/`Add-ItemTemplateSection` both return
`CommandNotFoundException`, and `Get-Command -Name "*Template*"` over the
same session lists no such cmdlets either). Earlier revisions of this skill
named them as if they were real SPE convenience cmdlets - they are not.
There is no higher-level "add a field to a template" cmdlet in SPE at all;
build Template Section/Template Field items the same low-level way as any
other item (see the example below), and use the real
`Add-BaseTemplate` cmdlet (confirmed live) for composing base templates:

```
Add-BaseTemplate -Item <TemplateItem> -Template <string[]>   # paths or IDs
Add-BaseTemplate -Item <TemplateItem> -TemplateItem <TemplateItem[]>
```

**Reference syntax for SPE cmdlets:** the official Sitecore PowerShell
Extensions documentation (https://doc.sitecorepowershell.com) is the
source of truth for exact cmdlet parameters - confirm against it (or
`Get-Command`/`Get-Help <cmdlet> -Full` on the *actual target instance*,
not just from memory) before relying on a remembered signature or cmdlet
name, per the correction above. The "Working with Items" page
(https://doc.sitecorepowershell.com/working-with-items) covers item
creation/editing patterns specifically - the closest match to the
`New-Item`/`Editing.BeginEdit()`/`Editing.EndEdit()` mechanics used
throughout this skill.

### Example: creating a template, rendering, and datasource item

Run everything against the remote session via SPE Remoting's
`Invoke-RemoteScript` - the script block executes on the Sitecore instance,
not locally. `$SxaSiteCollection`/`$SxaSite` are the Tenant/Site the user gave you -
pass them in explicitly, don't leave them to resolve from an outer scope.
System template IDs below (Template/Template Section/Template Field) are
Sitecore-standard, not solution-specific:

```powershell
$speSession = New-SPESession -Url $Url -Username $Username -Password $Password

Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($core, $area, $featureName, $renderingName, $sxaSiteCollection, $sxaSite)

    $templateTypeId = "{AB86861A-6030-46C5-B394-E8F99E8B87DB}"
    $sectionTypeId = "{E269FBB5-3750-427A-9149-7AA950B49301}"
    $fieldTypeId = "{455A3E98-A627-4B40-8035-E683A0331AC7}"

    $templateFolder = "master:/sitecore/templates/Feature/$core/$area/$featureName"
    $template = New-Item -Path $templateFolder -Name $renderingName -ItemType $templateTypeId

    $section = New-Item -Path $template.Paths.Path -Name "Data" -ItemType $sectionTypeId

    $field = New-Item -Path $section.Paths.Path -Name "Title" -ItemType $fieldTypeId
    $field.Editing.BeginEdit()
    $field["Type"] = "Single-Line Text"
    $field.Editing.EndEdit() | Out-Null

    $renderingFolder = "master:/sitecore/layout/Renderings/Feature/$core/$area/$featureName"
    New-Item -Path $renderingFolder -Name $renderingName -ItemType "/sitecore/templates/System/Layout/Renderings/View Rendering"

    $dataFolder = "master:/sitecore/content/$sxaSiteCollection/$sxaSite/Data/$core/$area/$featureName/$renderingName"
    New-Item -Path $dataFolder -Name "Sample $renderingName" -ItemType $template.ID
} -ArgumentList $Core, $Area, $FeatureName, $RenderingName, $SxaSiteCollection, $SxaSite
```

A field's `-Shared`/`-Unversioned` sharing is set the same way, directly on
the field item - not via a cmdlet switch (no such switch exists, per the
correction above):

```powershell
$field.Editing.BeginEdit()
$field["Type"] = "Integer"
$field["Shared"] = "1"          # Shared field - omit this line, or set "0", for a normal per-language field
$field.Editing.EndEdit() | Out-Null
```

Set the new rendering item's `Datasource Template`/`Datasource Location`
fields to point at the template and data folder created above so Content
Editor's "Insert options" and datasource picker offer them automatically.

### Serializing an item to disk - check for Unicorn first, don't default to `Export-Item`

**Before serializing anything, check whether the solution has Unicorn
configured for the target Sitecore path** - grep the solution for
`physicalRootPath` / `<configurations>` (Unicorn's own serialization config,
typically under an `App_Config/Include/Unicorn/**/*.Serialization.config`
or similarly-named file, one `<configuration name="..."><targetDataStore
physicalRootPath="..."/><predicate>...<include name="..." path="..."/>...`
block per logical grouping). If a `<predicate><include>` covers the path
you just created items under, **that configuration is the solution's real
serialization mechanism for this content** - use it (below), not SPE's own
`Export-Item`. This solution (SharpPS.Sitecore) uses **Unicorn**, confirmed
live: its config's `include name="Template.Feature.Maybank" path="/sitecore/
templates/Feature/Maybank"` and `include name="zzz.Content.Maybank" path="/
sitecore/content/Maybank"` map exactly onto this repo's own `items/Core/
Template.Feature.Maybank/...` / `items/Content/zzz.Content.Maybank/...`
folder layout - i.e. **the very YAML format this whole skill has been
reverse-engineering from existing files *is* Unicorn's Rainbow YAML
serialization**, not a bespoke or Sitecore-CLI format. Don't assume "no
`sitecore.json`/`*.module.json` found" means no serialization tooling is
configured - that's the Sitecore CLI's config format, a different (and, in
this solution, absent) mechanism; Unicorn's is XML, not JSON.

**When Unicorn covers the path, use its own SPE bridge cmdlet,
`Export-UnicornItem -Item <item> -Recurse`** (confirmed live, ships as part
of the solution's own Unicorn integration - `Get-Command -Name
"*Unicorn*"` lists it alongside `Sync-UnicornItem`/`Sync-UnicornConfiguration`
etc.), not SPE's own `Export-Item`. `Export-UnicornItem` resolves the
matching configuration automatically from the item's path and writes
through Unicorn's own configured `ITargetDataStore` (Rainbow's
`SerializationFileSystemDataStore`) - guaranteeing the output matches
what a real Unicorn sync would produce, in the exact format/layout already
in the repo, unlike hand-authoring YAML to match the format by eye:

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($itemPath)
    $item = Get-Item -Path $itemPath
    Export-UnicornItem -Item $item -Recurse
} -ArgumentList "master:/sitecore/templates/Feature/$core/$area/$featureName/$renderingName"
```

**Only fall back to SPE's own `Export-Item`** (`Spe.Commands.Serialization.
ExportItemCommand`) when no Unicorn (or equivalent) config covers the
target path at all - it serializes to Sitecore's older classic `.item` text
format via `Sitecore.Data.Serialization.Manager.DumpItem`, a different
format from Rainbow YAML and the wrong choice for a Unicorn-serialized
solution:

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($itemPath)
    Get-Item -Path $itemPath | Export-Item -Recurse
} -ArgumentList "master:/sitecore/templates/Feature/$core/$area/$featureName/$renderingName"
```

Both cmdlets write **on the Sitecore instance's own filesystem**, since the
script block runs server-side through `Invoke-RemoteScript` - not on
whatever machine started the SPE session, and (for a genuinely remote
instance, not a local one) not the same filesystem the local git repo lives
on at all. Retrieving the file(s) afterward needs one more step - see
below.

#### Finding where Unicorn actually wrote the files

`$(sourceFolder)`-style tokens in the `.config` file aren't resolved values
- get the real absolute path from the live configuration object instead of
guessing, since it may differ between environments (a remote dev instance's
own checkout path is not necessarily the same as the path on the machine
running these commands):

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    $config = Get-UnicornConfiguration | Where-Object { $_.Name -eq "Core.Website" }
    $targetDataStore = $config.Resolve([Unicorn.Data.ITargetDataStore])
    # ITargetDataStore is a ConfigurationDataStore wrapper - the real Rainbow
    # store (and its root path) is one level in, via .InnerDataStore
    $targetDataStore.InnerDataStore.PhysicalRootPath
}
```

**`PhysicalRootPath` is a public field, not a property** - it won't show up
under `Get-Member`/`.GetProperties()` defaults; access it directly
(`$store.PhysicalRootPath`) rather than reflecting for a "PhysicalRootPath"
*property* and getting a silent null back.

#### Filename truncation - a real item name doesn't always match its filename

Rainbow's `SerializationFileSystemDataStore` truncates long item names when
generating the on-disk filename (confirmed live: a field genuinely named
`OTR Price Error Required Message` - 33 characters - serialized to
`OTR Price Error Required Messa.yml`, a 30-character stem before `.yml`;
the item's actual Sitecore `Name` is untouched, only the filename is cut).
This matches this repo's own existing convention (multiple pre-existing
`.yml` filenames in `items/` are exactly 30 characters before the
extension) - so when programmatically locating a just-exported file by
name, don't assume `{item name}.yml` is always the real filename for names
approaching/exceeding ~30 characters; read back the actual directory
listing (`Get-ChildItem`) rather than constructing the expected filename
from the item name for anything long enough to be near that boundary.

#### Retrieving the exported files onto the machine that needs them

If the machine running these commands *is* the Sitecore instance's own
filesystem (a local dev instance), the files are already in place - nothing
more to do. For a genuinely remote instance (its own `Invoke-RemoteScript`
filesystem is not reachable as a local path - confirmed live for a
solution whose actual instance runs on a separate machine from where its
git repo checkout is being edited), retrieve them over the same SPE
Remoting connection rather than assuming file-share access:

- **`Receive-RemoteItem`** (a **local**, client-side SPE cmdlet - not run
  inside `Invoke-RemoteScript`) is the purpose-built tool for this: it
  downloads a file from the server through SPE's own web service endpoint.
  For a plain absolute server-side file path (not a Sitecore media item),
  pass it directly as `-Path` with no `-RootPath` needed (`-RootPath` is
  only for a small fixed set of keyword-relative locations - `App`, `Data`,
  `Media`, `Serialization`, etc. - and is required only when `-Path` isn't
  already a fully-qualified path):

  ```powershell
  Receive-RemoteItem -Session $speSession `
      -Path "C:\Projects\Solution\items\Core\...\SomeField.yml" `
      -Destination "C:\LocalRepo\items\Core\...\SomeField.yml" -Force
  ```

  It also accepts a list of server paths over the pipeline (e.g. from an
  `Invoke-RemoteScript` call that returns matching file paths via
  `Get-ChildItem ... | Select-Object -Expand FullName`), downloading each
  in turn - useful for pulling every file Unicorn just wrote in one step,
  though each still needs its own `-Destination` folder or `-Container` to
  preserve structure. Confirmed live to exist and documented (source:
  https://doc.sitecorepowershell.com/appendix/common/receive-file describes
  `Receive-File`, a *different*, upload-only, interactive-dialog cmdlet
  that doesn't work over `Invoke-RemoteScript` at all - don't confuse the
  two by name similarity; `Receive-RemoteItem` is the download one).
- If `Receive-RemoteItem` isn't available or convenient for the number of
  files involved, the same result is achievable by having
  `Invoke-RemoteScript` itself return each file's content as a string
  (`Get-Content $path -Raw`) and writing it locally from the returned
  value - confirmed live to work end-to-end for dozens of files at once,
  though it's a workaround rather than the purpose-built mechanism above.
  Whichever approach is used, verify the retrieved content against a few
  known-good existing files in the repo afterward (matching field-sharing
  conventions, ID formatting, alphabetical field ordering) rather than
  assuming the transfer preserved everything correctly.

## Cmdlets available once imported

- `Start-Pipeline -Name Sitecore` - deploy the Sitecore solution
- `Start-Pipeline -Name Publish -Args @{ PublishUrl = "C:\Custom\Path" }` - publish to a specific path
- `Invoke-Migration` - run database migration
- `Invoke-SyncUnicorn -Url "https://cm.sitecore.dev"` - sync Unicorn serialization
- `Start-SiteUp -Url "https://cm.sitecore.dev"` - warm up the site
