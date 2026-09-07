---
name: feature-foundation-project
description: Use when adding a new Feature or Foundation layer project to an existing SharpPS Sitecore solution via the "Sitecore MVC" VS project template (SitecoreProjectWizard). Covers the naming/location convention, how SharpPS.config supplies the wizard's defaults instead of prompting, and Feature's automatic ProjectReference to the Foundation project.
---

# Creating a new Feature or Foundation project

This is about adding a **module** to an existing solution - Visual Studio's
"Add New Project" -> **Sitecore MVC** template
(`Sitecore.MVC.vstemplate`, `TemplateID: SharpPS.Sitecore.Project.MVC`,
wizard `SitecoreProjectWizard`). It's not the one-time root website project
created when the solution itself is first scaffolded (that's a separate
template/wizard).

## Workflow: Spec -> Plan -> Execution

**Spec - ask the user if any of this is missing, don't assume:**
- Layer: Feature or Foundation
- `<Name>` (the module name, e.g. `Content`, `Search`)
- Whether `SharpPS.config` already exists at the solution root (if it
  doesn't, the values in the table under "SharpPS.config supplies the rest"
  below have to come from the user instead of being read automatically)

**Plan - resolve before creating anything:**
1. Project name = `$solutionpathformat$.{Layer}.<Name>`, location =
   `src\{feature|foundation}\<Name>` (table below)
2. List the target paths that will be created - the "What gets scaffolded"
   table below, with `$solutionpathformat$`/`$mvc_area$`/`$projectkey$`
   resolved to real values
3. If Layer is Feature: locate the Foundation project to reference (
   `SharpPS.config`'s `foundationpath`, else the solution's
   `*.Foundation.csproj`) - if none exists, say so before proceeding rather
   than silently creating an unreferenced Feature project
4. Decide the source for file content: an existing sibling Feature/Foundation
   project to copy (preferred - see below), or hand-authored from the
   target-path table if none exists yet

**Execution:**
1. Create the project folder/files at the resolved location
2. Wire the `.csproj`: `<ProjectReference>` to Foundation (Feature only),
   `<PackageReference>` items if Foundation (Feature gets none - see
   "Feature projects auto-reference..." below)
3. Add the project to the solution file
4. Report back the concrete paths/name actually used, not the token form

## Without the VS wizard: copy a sibling project, don't hand-author from scratch

This skill documents the wizard's *conventions* (naming, target paths,
`SharpPS.config` mapping, the auto `ProjectReference`) - it does **not**
embed the actual file *contents* (the boilerplate inside
`Area.Settings.config`, `ServiceConfiguration.cs`, `FeatureController.cs`,
etc.). Those source templates live in `SharpPS.VisualStudio.Sitecore.
Templates\MVC\*` in the separate VS extension repo, which isn't available
from inside a generated solution - only this `SKILL.md` ships there, not the
template sources it was written from.

So without the VS wizard: if a sibling Feature (or Foundation) project
already exists in the solution, **copy its structure and adapt it** (rename
namespaces/tokens per the naming convention below) - that's the intended
approach, not a fallback, since it's the only actual source of correct file
content available at that point. Only hand-author a file from scratch,
using the target-path table and conventions below as a guide, when no
sibling project exists yet to copy from.

## Naming and location convention

| Layer | Project name | Location |
|---|---|---|
| Feature | `$solutionpathformat$.Feature.<Name>` | `src\feature\<Name>` |
| Foundation | `$solutionpathformat$.Foundation.<Name>` | `src\foundation\<Name>` |

The user supplies `<Name>` (and picks Feature vs Foundation) - everything
else about which layer it is comes from that name, not any checkbox in the
wizard: `SitecoreProjectWizard.PrepareStarting` sets `isFeatureProject =
$safeprojectname$.Contains(".Feature.") || .Contains(".UnitTests.")`.

## What gets scaffolded

`Sitecore.MVC.vstemplate`'s `TemplateContent` is static - it creates the
same project items every time, regardless of whether the name is `.Feature.`
or `.Foundation.`:

| Target path | Source | Notes |
|---|---|---|
| `App_Config\Include\Feature\$solutionpathformat$\$safeprojectname$.Area.$mvc_area$.Settings.config` | `Area.Settings.config` | |
| `App_Config\Include\Feature\$solutionpathformat$\$safeprojectname$.ServiceConfigurator.config` | `Feature.ServiceConfigurator.config` | |
| `$mvc_area$\Views\$projectkey$\README.md` | `Areas\ViewsREADME.md` | |
| `$mvc_area$\Controllers\$projectkey$Controller.cs` | `Areas\FeatureController.cs` | derives from the Foundation project's `BaseController` |
| `DependencyInjection\ServiceConfiguration.cs` | same | implements `SharpPS.DependencyInject.IService*` |
| `AssemblyInfo.cs`, `FolderProfile.pubxml`, `favicon.ico` | same | |
| `$mvc_area$\Views\Web.config` | `Areas\Web.config` | build action `Content` - **does** get published (blocks direct URL access to `.cshtml` under that Area's Views) |
| `Views\Web.config`, `Web.config`, `Web.Debug.config`, `Web.Release.config` | same | build action `None` in `ProjectTemplate.csproj` - scaffolded so VS treats this as a valid Web Application project, but **excluded from publish output**; the actual runtime `Web.config` is the host site project's |
| Empty folders: `Models`, `Views\Shared`, `Configuration`, `Services`, `Pipelines` | - | scaffolded but empty |

**Quirk to know:** the two `App_Config\Include` config `TargetFileName`s
hardcode an `Include\Feature\...` path segment unconditionally - a project
named `$solutionpathformat$.Foundation.<Name>` still gets its configs placed
under `App_Config\Include\Feature\$solutionpathformat$\...`, not
`Include\Foundation\...`. That's the template's actual behavior, not a typo
to "fix" when replicating it by hand.

## SharpPS.config supplies the rest - no prompting if it's already there

If `SharpPS.config` exists at the solution root, `SitecoreProjectWizard.
LoadFromConfig` reads it directly and the "Sitecore Project MVC Setup" UI
form is skipped entirely:

| SharpPS.config key | Wizard token |
|---|---|
| `version` | `$sc_version$` |
| `url` | `$sc_url$` |
| `area` | `$mvc_area$` |
| `publishpath` | `$sc_publishpath$` |
| `framework` | `$targetframeworkversion$` |
| `core` | `$solutionpathformat$` |
| `dbprovider`/`dbpackage`/`dbpackageversion` | DB connection defaults |
| `foundationpath` | Foundation project override (see below) - not present in `SharpPS.config` by default; add it by hand only if auto-discovery picks the wrong project |

If `SharpPS.config` doesn't exist yet (e.g. very first module added to a
fresh solution), the setup form prompts for these values instead, and
`SitecoreProjectWizard.GenerateConfigurationFile` then writes
`SharpPS.config`/`nuget.config` to the solution root from that input so every
later project add skips the prompt.

## Feature projects auto-reference the Foundation project

Only when `isFeatureProject` is true: the wizard resolves the Foundation
project's `.csproj` - `SharpPS.config`'s `foundationpath` if set, otherwise
the first `*.Foundation.csproj` found anywhere under the solution directory
- and injects a `<ProjectReference>` to it automatically. If no Foundation
project can be found anywhere in the solution, `isFeatureProject` is forced
back to `false` (no reference gets added). Foundation projects never get
this reference (there's nothing else in the solution for a Foundation
project to depend on).

This also affects package restore: Feature projects get **no** packages from
the vstemplate's own `<WizardData><packages>` list (they inherit
`Sitecore.Mvc`/`Microsoft.AspNet.Mvc` transitively through the referenced
Foundation project); Foundation projects get that full package list.

## Project file format

`ProjectTemplate.csproj` (the generated project's `.csproj`) is a classic
non-SDK-style .NET Framework project (`ToolsVersion="15.0"`,
`TargetFrameworkVersion=v$targetframeworkversion$`, explicit `Import`s of
`Microsoft.Common.props`/`Microsoft.CSharp.targets`/
`Microsoft.WebApplication.targets`) but sets `<RestoreProjectStyle>
PackageReference</RestoreProjectStyle>` - so NuGet packages are `<PackageReference>`
items, not a `packages.config` file. The wizard injects them (and the
Foundation `<ProjectReference>` from the section above) into a single
`<ItemGroup>` via two template tokens it fills in itself:

```xml
<ItemGroup>
  $packagereference$
  $projectreference$
</ItemGroup>
```

To add/remove a package on a generated project, edit its `<PackageReference>`
items directly in the `.csproj` - there's no `packages.config` to touch.
