# Template, rendering, and datasource item creation

Before execution, read [SPE remoting](../../sitecore-spe-remoting/SKILL.md) for connection prerequisites and live-write authorization. This recipe is not permission to modify an instance. Approve the target and item design before writing; for HTML conversion use [rendering-and-datasource](../../rendering-and-datasource/SKILL.md). The creation example assumes parent folders exist and illustrates a View Rendering; detect the required rendering type before using it.

## CMS content-tree conventions (templates, renderings, datasources)

### Workflow: Spec -> Plan -> Execution

**Spec - ask the user if any of this is missing, don't guess:**
- Tenant (`{site-folder}`) and Site (`{sxa-site}`) - never assume there's
  only one
- Feature name and Rendering name the template/rendering/datasource belong to
- Sitecore credentials, only if authentication fails after resolving explicit
  overrides, `SharpPS.config` values, and defaults in [solution configuration](../../sitecore-solution-config/SKILL.md)
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
used throughout this solution's config/rendering paths (see [solution configuration](../../sitecore-solution-config/SKILL.md)). `{site-folder}` (the Tenant)
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
  when the user authorized live creation, use the SPE session below rather
  than stopping at manual Content Editor instructions:
  - `New-SitecoreSession` (see [connections](../../sitecore-spe-remoting/SKILL.md)) only gets you an authenticated
    `WebRequestSession` for HTTP calls to existing admin pages - it can't
    create items on its own.
  - `New-SPESession` (wraps Sitecore PowerShell Extensions' Remoting module -
    `Import-Module SPE; New-ScriptSession -Username ... -Password ...
    -ConnectionUri $Url`) opens a **remote PowerShell session** into the
    instance, letting you run arbitrary Sitecore PowerShell (`New-Item`,
    etc.) against the content tree remotely. Defaults to
    `sitecore\admin`/`b` if `-Username`/`-Password` aren't passed. Resolve
    credentials from `SharpPS.config` first (see [solution configuration](../../sitecore-solution-config/SKILL.md)), then pass them
    explicitly so configured values override these defaults.
  - **`-Password` here is a plain `[string]`, not a `SecureString`** -
    unlike HTTP `New-SitecoreSession` (whose `-Password` *is* a
    `SecureString`, requiring `ConvertTo-SecureString` first). Pass the
    plain password directly to `New-SPESession -Password $Password`; don't
    reuse a `ConvertTo-SecureString`'d value from the `New-SitecoreSession`
    flow - a `SecureString` bound to a `[string]` parameter stringifies to
    `System.Security.SecureString`, so the remoting endpoint receives that
    literal text instead of the password and authentication fails silently
    with no obviously-related error.
  - If the resolved credentials fail, ask the user for corrected credentials
    rather than retrying defaults or giving up on item creation entirely.
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
# $Username/$Password are resolved using sitecore-solution-config.
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
