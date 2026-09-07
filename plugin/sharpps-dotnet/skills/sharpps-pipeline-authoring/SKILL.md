---
name: sharpps-pipeline-authoring
description: How to author a correct SharpPS.Shells pipeline in a workspace — when a pipeline is the right shape vs a public function, the folder/processor conventions, the 00-Help / 01-Resolve-Configuration patterns, sharpps.config-driven per-project settings, abort semantics, and the verification checklist before shipping. Use when the user asks to create/add/write a pipeline or processor for SharpPS.Shells, wonders "pipeline or function?", or wants project-level (workspace) pipelines. For running, inspecting, or runtime-patching already-registered pipelines, use the sibling `sharpps-pipeline` skill instead.
---

# Authoring a SharpPS.Shells pipeline in a workspace

This skill is about *writing* pipelines correctly. The sibling `sharpps-pipeline` skill covers the
engine (`Register-Pipeline`/`Start-Pipeline`/`Get-Pipeline`/`Update-Pipeline`) — read it for how
registration and execution work; read this one before creating new pipeline folders/processors.

## Rule 0 — pipeline or public function?

The module's architecture rule (set by its author):

- **Public function** (`Functions/Verb-Noun.ps1`) — a single capability, called directly and
  globally: composable, tab-completed parameters, `-WhatIf`, usable in any script. If the thing
  is one step, it is a function. **Never create a pipeline whose processors merely translate
  `@{ Key = ... }` into one function's parameters — that is a layer, not a pipeline.**
- **Pipeline** (`Pipelines/<Name>/NN-*.ps1`) — an *ordered sequence* with shared state and abort
  semantics: step 2 must not run if step 1 failed, later steps read what earlier steps resolved.
  Processors **orchestrate public functions; functions do the work** (the shipped `sitecore`
  pipeline calls `Invoke-SitecorePublish`/`Invoke-SyncUnicorn`; the `deploy` pipeline calls
  `Publish-Artifact`-style copy + `Get-DeployDrift` + `Find-LogError`).

Also never ship a function whose body is one obvious command the user already types
(`docker logs`, `docker exec ... bench`) — wrap only sequences, incantations nobody remembers,
or logic (parsing, hashing, polling).

## Rule 1 — the module is stack-neutral and machine-neutral

`SharpPS.Shells` serves Sitecore, Liferay, and future stacks from one codebase, installed on any
machine. Therefore, in module code (`Functions/`, `Pipelines/`):

- **No absolute paths of any machine.** Not even as parameter defaults.
- **No stack-specific defaults** (no `/opt/liferay/...`, no IIS paths). If a step needs one,
  it comes from configuration; when it is missing, **skip that step gracefully with a message
  that names the exact key to add** — do not throw, do not guess.
- Per-**project** settings → `sharpps.config` (lowercase filename, XML, read from the current
  directory). Per-**machine** settings → environment variables. Per-**call** → parameters/
  `$arguments` (always win over config).

## Workspace layout and registration

A workspace (project repo) can carry its own pipelines — they do not have to live inside the
module:

```
MyWorkspace/
  sharpps.config              # per-project settings (see below)
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

First file is always `00-Help.ps1` — prints usage and aborts, so `Start-Pipeline <name> -Help`
never executes real steps:

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
(a "Docker" banner rendered as "Doker"). Verify by dot-sourcing the file with
`@{ Help = $true }` and reading the output.

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

Established `sharpps.config` keys (add your own as lowercase elements under `<configuration>`):

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

## Chaining pipelines

Two mechanisms, both sharing the same `$arguments`:

```powershell
# a) a delegating processor (e.g. Liferay/Frappe forwarding Service/Log/Restart keys to docker):
$isVerbose = $VerbosePreference -eq "Continue"
Start-Pipeline docker -Verbose:$isVerbose -Args $arguments

# b) registration-time dependency — every run of this pipeline runs startup first:
Register-Pipeline -BasePath ./Pipelines -Predecessors startup -Force
```

Prefer (a) when only *some* trigger keys should forward; (b) when the other pipeline must
always complete first.

## Verification checklist before calling it done

Run every one of these — each catches a class of bug that has actually occurred:

1. `Import-Module ./SharpPS.Shells.psd1 -Force` (or `Register-Pipeline ... -Force`) — parses
   cleanly, pipeline appears.
2. `Start-Pipeline <name> -Help` — banner renders un-mangled, usage lines match real keys, and
   **nothing else runs** (Help must abort the chain).
3. `Start-Pipeline <name>` with empty/zero config in an empty directory — every step either
   works or aborts with a message naming the missing key; no unhandled exceptions.
4. Force each failure path (bad build command, missing artifact, wrong container) — verify the
   chain stops where it should and later steps are skipped.
5. The success path end-to-end — but **never against a real target the user didn't ask to
   touch**: simulate the environment-changing part (scratch folders, a byte-identical artifact,
   a background job standing in for the consumer) and leave the first real run to the user.
6. Sweep for leaked specifics: `grep -rin "liferay|sitecore|/opt/|C:\\\\" <new files>` must come
   back empty (examples in help text use neutral placeholders like `myservice`).

## Reference implementation

`SharpPS.VisualStudio/SharpPS.Shells/Pipelines/Deploy/` is the canonical worked example — a
stack-neutral hot-deploy loop (resolve config → build → clear container log → copy → poll-verify
by hash → error report) where every processor follows the rules above and all real work lives in
public functions (`Clear-DockerLog`, `Get-DeployDrift`, `Find-LogError`).
