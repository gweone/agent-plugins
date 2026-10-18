# Configuration, failure handling, and native commands

External source/version examples, not freshly verified runtime. In module code, never use
machine-specific absolute paths or stack-specific defaults. Project config is lowercase XML
`sharpps.config` in the current directory; machine settings use environment variables; explicit
per-call `$arguments` win. Missing optional configuration should skip gracefully and name the
exact key; a required-operation failure should warn, set `Aborted`, and return.

## Standard processor 01: Resolve-Configuration

Second file fills `$arguments` from `sharpps.config`, **only for keys not already passed** —
explicit arguments always beat config (same pattern as the shipped Sitecore/SIF/Artifact
pipelines):

```powershell
if (-Not (Test-Path -Path "sharpps.config")){
    return
}
[xml]$config = Get-Content "sharpps.config"
if(-not $arguments.ContainsKey("Artifact") -and $null -ne $config.configuration.artifact){
    $arguments["Artifact"] = @($config.configuration.artifact)
}
# ...one block per key
```

Keys documented in the external source/workspace examples (add your own as lowercase elements
under `<configuration>`). `deploy`, `docker`, and their helper functions are version/workspace
examples, not guaranteed members of the installed shipped catalog:

| Key | Meaning | Used by |
|---|---|---|
| `url`, `core`, `publishpath`, `username`, `password` | Sitecore instance settings | `sitecore`/`publish`/`artifact` pipelines |
| `artifact` | glob(s) of built artifact(s), repeatable element | `deploy` pipeline, `Publish-Artifact`, `Get-DeployDrift` |
| `deploypath` | hot-deploy folder the runtime watches | same |
| `container` | docker container name | same + `Find-LogError`/`Clear-DockerLog` steps |
| `containerpath` | where the runtime keeps *loaded* artifacts inside the container | `Get-DeployDrift` verify step |
| `build` | the project's build command line | `deploy` pipeline, `Publish-Artifact -Build` |

## Failing correctly: Aborted, not throw

A processor that hits a hard failure should **warn and abort, then return** — not throw:

```powershell
if ($somethingRequired -eq $null)
{
	Write-Warning "Nothing to deploy. Pass Artifact/DeployPath or add <artifact>/<deploypath> to sharpps.config."
	$arguments["Aborted"] = $true
	return
}
```

`Start-Pipeline` skips every later non-`AlwaysRun` processor once `Aborted` is set, but
`AlwaysRun` cleanup/report steps still execute — a `throw` would kill those too. The warning
must always name the exact parameter/config key that fixes the problem.

## Running native commands (build steps) — two real gotchas

```powershell
$global:LASTEXITCODE = 0            # (1) pure-PowerShell commands never set it — reset first,
try                                  #     or a stale/unset value gives a false verdict
{
	$ErrorActionPreference = "Stop"  # (2) command-not-found is non-terminating by default:
	Invoke-Expression $arguments["BuildCommand"]   # it prints red and KEEPS GOING unless EAP=Stop
}
catch
{
	Write-Warning "Build failed: $_"
	$arguments["Aborted"] = $true
	return
}
finally
{
	$ErrorActionPreference = "Continue"
}
if ($LASTEXITCODE -ne 0)
{
	Write-Warning "Build failed with exit code $LASTEXITCODE"
	$arguments["Aborted"] = $true
}
```

Both were found by testing, not review: without (1) an `echo`-style build "succeeds" with a
phantom failure; without (2) a typo'd build command prints an error and the pipeline happily
deploys nothing.

## Command configuration is trusted code

`Invoke-Expression $arguments["BuildCommand"]` executes arbitrary PowerShell. Only use this
legacy build-command pattern with explicitly trusted and reviewed arguments/configuration;
never interpolate untrusted input or treat XML as inert when it feeds command execution.
Prefer a fixed executable and an explicit argument array with `&` where possible. The example
resets `$ErrorActionPreference` to `Continue`; production code should save the prior preference
and restore it in `finally` rather than overwrite caller policy. `$LASTEXITCODE` detects native
exit failures, not every possible pure-PowerShell semantic failure; validate actual outputs.

`Aborted` does not undo work already done and does not suppress `AlwaysRun`. Cleanup/reporting
processors must be safe for partial state and explicitly audited for their own effects.

Source traces: external `SharpPS.Shells/Pipelines/` Sitecore/SIF/Artifact config resolvers and
`Deploy/` processor/helper examples. Claims of prior testing above describe the original
source guidance, not tests performed during this documentation refactor.

- [Layout/processors](layout-and-processors.md).
- [Chaining/verification](chaining-and-verification.md).
- [Authoring entrypoint](../SKILL.md).
