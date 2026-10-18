# SharpPS solution configuration

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

### SPE credentials: resolve from SharpPS.config before connecting

The solution-root `SharpPS.config` is optional for SPE authentication. If
the file does not exist, use the cmdlet defaults (`sitecore\admin` / `b`)
unless the user explicitly supplies overrides; do not require creating the
file or ask for credentials just because it is absent.

When present, `SharpPS.config` can override SPE credentials with
`<username>` and `<password>` elements directly under `<configuration>`.
Resolve each value independently: an explicit user-supplied override takes
precedence, then a populated config element, then the cmdlet default
(`sitecore\admin` for SPE username, `b` for password). A config containing
only `<password>` therefore overrides the password while keeping the
default username. Do not try default credentials first when configured
values are available, or ask for credentials already present in this file.

For direct SPE calls, read the config and pass the resolved values explicitly;
do not assume `New-SPESession` reads `SharpPS.config` itself. This example
uses config values with defaults; apply any explicit user override afterward:

```powershell
$Username = 'sitecore\admin'
$Password = 'b'
$configPath = Join-Path $SolutionPath 'SharpPS.config'
if (Test-Path -LiteralPath $configPath) {
    [xml]$solutionConfig = Get-Content -LiteralPath $configPath -Raw
    if (-not [string]::IsNullOrWhiteSpace([string]$solutionConfig.configuration.username)) {
        $Username = [string]$solutionConfig.configuration.username
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$solutionConfig.configuration.password)) {
        $Password = [string]$solutionConfig.configuration.password
    }
}
# Apply the certificate-trust setup from sitecore-spe-remoting in this same process if needed.
$speSession = New-SPESession -Url $Url -Username $Username -Password $Password
```

Preserve configured values as written, including password whitespace; do
not print credentials or copy actual values into scripts, documentation,
or permission entries. If authentication fails with the resolved credentials,
ask for corrected values rather than retrying with defaults.

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

### Automation scope and authorization

PowerShell `Start-Pipeline` deployment/publish workflows use `SharpPS.Shells`,
not Sitecore's C# `CorePipeline` engine. Inspect installed command help and
registered processors/predecessors before running them; even `Start-Pipeline -Help`
may execute predecessors or custom steps.

The imported module also exposes `Invoke-Migration`, `Invoke-SyncUnicorn`,
and `Start-SiteUp`; verify their installed help and actual target before use.
These configuration notes are not a full deployment, publishing, or warm-up guide.

Live writes require explicit user authorization. Never infer an instance,
Tenant/Site, or permission to change shared infrastructure from choosing a skill
or resolving configuration values.
