# Workspace layout and processors

Use this for persistent workspace files in **SharpPS.Shells** PowerShell, not C#
`SharpPS.Pipeline` or Sitecore `CorePipeline`. Examples are historical external source guidance,
not newly verified runtime behavior. Agree file targets first; registration and execution are
separate authorized operations. Inspect source/`Get-Pipeline` before running any Help example.

Processors orchestrate public functions: the documented `sitecore` processors call
`Invoke-SitecorePublish`/`Invoke-SyncUnicorn`; the version/workspace `deploy` example combines
`Publish-Artifact`-style copy, `Get-DeployDrift`, and `Find-LogError`. These are source traces,
not a guarantee that those commands exist in the installed version.

Project settings are covered in [configuration and failure](configuration-and-failure.md).

## Workspace layout and registration

A workspace (project repo) can carry its own pipelines — they do not have to live inside the
module:

```
MyWorkspace/
  sharpps.config              # per-project settings (configuration reference)
  Pipelines/
    release/
      00-Help.ps1
      01-Resolve-Configuration.ps1
      02-Build.ps1
      03-Package.ps1
      04-Verify.ps1
```

```powershell
Register-Pipeline -BasePath ./Pipelines -Force     # folder name → pipeline name (lower-cased)
Start-Pipeline release -Help
```

Ordering is **purely alphabetical on filename** — the `NN-` prefix is the only ordering
mechanism. A filename containing the literal substring `AlwaysRun` marks that processor to run
even after an abort (use for cleanup/reporting steps). Note the shipped `publish` pipeline's
`01-Startup.ps1` also auto-registers any `Pipelines/` folders it finds under the solution
directory — workspace pipelines get picked up when developers run the standard flows.

## The processor template

Every processor has exactly this shape (tab-indented param block is house style):

```powershell
[CmdletBinding()]
param(
	[hashtable]$arguments
)

if($arguments.ContainsKey("MyTriggerKey"))
{
	# read/write shared state via $arguments; call public functions for the real work
}
```

Processors are dot-sourced with the *same* `$arguments` hashtable, so anything you set is visible
to every later processor (and to chained pipelines). Gate each optional step on its own trigger
key so `Start-Pipeline name @{ OnlyThis = $true }` runs just the relevant steps.

## Standard processor 00: Help

First file is always `00-Help.ps1` — prints usage and aborts ordinary subsequent steps. This is the intended convention, **not a
universal no-side-effects guarantee** for `Start-Pipeline <name> -Help`: predecessors execute
before the engine sets `Help`, and `AlwaysRun` processors may execute after abort. Read the
Help source and registered graph first; only run the example in an authorized isolated fixture:

```powershell
if($arguments.ContainsKey("Help")){
	Write-Host @"
          ...ascii banner...
"@ -ForegroundColor Red
	Write-Host "Usage :" -ForegroundColor Yellow
	Write-Host "Start-Pipeline release @{ Build = `$true }" -ForegroundColor Magenta -NoNewline
	Write-Host "`t What it does"
	$arguments["Aborted"] = $true
}
```

Gotcha (hit for real): **no backtick characters inside the ASCII banner** — inside a
double-quoted here-string PowerShell eats them as escapes and silently corrupts the art
(a "Docker" banner rendered as "Doker"). After reviewing the file for side effects, verify in an authorized isolated fixture by
dot-sourcing it with `@{ Help = $true }` and reading the output.

## Source traces and related lookup

- External `SharpPS.Shells/Pipelines/Publish/01-Startup.ps1`: solution workspace auto-registration
  described above is version-specific, not a guarantee for every installed version.
- `Register-Pipeline` sorts full file paths alphabetically; the numeric prefixes encode order.
- [Configuration/failure handling](configuration-and-failure.md).
- [Chaining/verification](chaining-and-verification.md).
- [Authoring entrypoint](../SKILL.md).
