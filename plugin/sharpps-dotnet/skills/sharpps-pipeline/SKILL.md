---
name: sharpps-pipeline
description: Use when working with the SharpPS.Shells PowerShell module — its `Register-Pipeline`, `Start-Pipeline`, `Get-Pipeline`, `Update-Pipeline` cmdlets, the `Pipelines/{name}/NN-*.ps1` folder convention, or SharpPS pipelines named `artifact`, `install`, `publish`, `sif`, `sitecore`, `startup`, `traefik`. Covers how the module auto-registers pipelines on import, how `Start-Pipeline` walks predecessors and processors sharing one `$arguments` hashtable, the `AlwaysRun`/`Aborted`/`Help` short-circuit convention, and — the "patch" workflow — how to reshape an already-registered pipeline at runtime with `Update-Pipeline` (`Replace`, `InsertBefore`, `InsertAfter`, `MoveTo`, `Remove`) without editing the shipped `.ps1` files. Triggers on "SharpPS pipeline", "Start-Pipeline", "Register-Pipeline", "Update-Pipeline", "pipeline processor", "patch the pipeline", "add a step to the pipeline".
---

# SharpPS.Shells pipeline system

## Workflow

This skill follows the plugin's standard **Spec → Plan → Execution** convention — never jump
straight to running `Start-Pipeline`/`Update-Pipeline`/`Register-Pipeline`. This matters more
here than for a single CLI tool: several shipped pipelines perform real, consequential actions
(`sitecore` publishes + runs a DB migration + syncs Unicorn; `artifact` archives and can build
migration scripts; `install`/`sif` install software) — not read-only inspection.

1. **Spec** — resolve which operation is wanted before doing anything: install/register the
   module (one-time setup), run an existing pipeline (`Start-Pipeline <name>`, and with which
   `$arguments`/predecessors), inspect one (`Get-Pipeline`), patch an already-registered one at
   runtime (`Update-Pipeline` — Replace/InsertBefore/InsertAfter/MoveTo/Remove), or register a
   brand-new one from a custom folder. Ask the user if the target pipeline or arguments are
   ambiguous rather than guessing — especially before touching one of the pipelines with real
   side effects listed above.
2. **Plan** — state the exact cmdlet invocation that will run — which PowerShell host (see
   below), pipeline name, the full `$arguments` hashtable, any `-Predecessors`, and for
   `Update-Pipeline` which processor and which action — before running it. If the pipeline
   performs a real action (deploy, install, DB migration, archive), say so explicitly as part of
   the Plan so it isn't a surprise.
3. **Execution** — run the cmdlet from the Plan and report the result (which processors ran,
   whether `Aborted`/`Help` short-circuited early, and any output the pipeline produced).

## Which PowerShell host to invoke

`SharpPS.Shells` is cross-platform (the `install` pipeline explicitly branches Chocolatey vs.
native Linux/macOS package managers), so don't default to one launcher name without checking:

- **Windows**: both `powershell` (Windows PowerShell 5.1 — built in, legacy) and `pwsh`
  (PowerShell 7+/Core, if installed) may be present. Prefer `pwsh` unless the user explicitly
  asks for Windows PowerShell — it's the actively-maintained line and the same one required on
  Linux/macOS, so defaulting to it keeps behavior consistent across OSes.
- **Linux/macOS**: only `pwsh` exists — there is no `powershell` binary at all. The module
  targets `netstandard2.0` so it loads under either host, but only `pwsh` runs outside Windows in
  the first place.

When invoking a cmdlet from a non-PowerShell shell (e.g. this Bash tool, a CI step), call the
host explicitly rather than assuming the ambient shell already is PowerShell:

```bash
pwsh -NoProfile -Command "Start-Pipeline sitecore @{ PublishUrl = 'C:\Custom\Path' } -Verbose"
```

If the user is specifically working inside a Windows PowerShell 5.1 session (not `pwsh`), swap
`pwsh` for `powershell` in the invocation above — the cmdlets themselves behave the same either
way, only the host binary name changes.

`SharpPS.Shells` is a PowerShell module (`SharpPS.Shells.psd1`/`.psm1`, `netstandard2.0` compiled
cmdlets + shipped `.ps1` scripts) built around one idea: a **pipeline** is a named, ordered list of
scripts (*processors*) that all receive the same shared `[hashtable]$arguments`, so each step can
read what an earlier step decided and write flags later steps react to (most importantly
`Aborted`).

On import, `SharpPS.Shells.psm1`:
1. Loads the compiled `SharpPS.Shells.dll` (the cmdlets below) and dot-sources every
   `Functions/*.ps1` (public helpers, e.g. `Invoke-MSBuild`, `Invoke-SyncUnicorn`) and
   `Privates/*.ps1` (internal helpers).
2. Runs `Register-Pipeline -BasePath Pipelines -Force`, which registers every pipeline the module
   ships out of the box: `artifact`, `install`, `publish`, `sif`, `sitecore`, `startup`, `traefik`.

## Installing the module: the SharpPS gallery, not the public NuGet gallery

`SharpPS.Shells` is published to **`SharpPSGallery`**, a MyGet-backed PowerShell repository —
`https://www.myget.org/F/sharpps/api/v2` — not PSGallery/nuget.org. Register that repository once,
then `Install-Module` from it, exactly as the Sitecore template's bootstrap script does (in that
repo: `SharpPS.VisualStudio.Sitecore.Templates/items/tools/powershell/launcher.ps1`):

```powershell
$Repository    = "SharpPSGallery"
$RepositoryUrl = "https://www.myget.org/F/sharpps/api/v2"

if (-not (Get-PSRepository -Name $Repository -ErrorAction SilentlyContinue)) {
    Register-PSRepository -Name $Repository -SourceLocation $RepositoryUrl -InstallationPolicy Trusted
}

# Idempotency check used by launcher.ps1: only install if Start-Pipeline isn't already available.
if (-not (Get-Command -Name Start-Pipeline -ErrorAction SilentlyContinue)) {
    Install-Module SharpPS.Shells -Repository $Repository -Force -Confirm:$false -Scope AllUsers
}

Import-Module SharpPS.Shells
```

- `-InstallationPolicy Trusted` is required once at registration time — `SharpPSGallery` isn't a
  trusted repo by default, so a plain `Install-Module` against it prompts/fails otherwise.
- `-Scope AllUsers` (as used in `launcher.ps1`) needs an elevated/administrator shell; drop it (or
  use `-Scope CurrentUser`) for a per-user install that doesn't need elevation.
- Gate on `Get-Command Start-Pipeline` (not `Get-Module -ListAvailable`) to check whether the
  module is already usable in the current session before reinstalling — that's the check
  `launcher.ps1` uses.
- If registering against `SharpPSGallery`/MyGet fails on TLS/certificate errors (seen on older
  PowerShell/.NET on some machines), `launcher.ps1` also ships a `Set-CertificatePolicy` helper
  that relaxes `ServicePointManager` TLS/cert validation before registering — only reach for that
  on a machine where you've hit that specific failure, not as a default.
- This is a distinct package/repository from the generic `NugetGallery`-hosted
  `SharpPS.PowerShell.MSBuild` module documented in `SharpPS.Shells/docs/README.md` — don't
  conflate the two; `SharpPS.Shells` (the pipeline module this skill covers) lives on
  `SharpPSGallery`.

## The four cmdlets

| Cmdlet | Purpose |
|---|---|
| `Register-Pipeline -BasePath <dir> [-Force] [-Predecessors <name[]>]` | Scans `<dir>` and (re)builds the in-memory pipeline table from it. |
| `Start-Pipeline <Name> [-Args <hashtable>] [-Predecessors <name[]>] [-Help] [-Verbose]` | Runs a registered pipeline's processors in order. |
| `Get-Pipeline -Name <name>` | Returns the pipeline's `Processor[]` so you can inspect or pipe it into `Update-Pipeline`. |
| `Update-Pipeline -Processor <p> [-Path <script> -Action Replace\|InsertBefore\|InsertAfter] [-MoveTo <int>] [-Remove] [-Predecessors <name[]>]` | Mutates a registered pipeline **in the current session** — the "patch" operation. |

All pipeline names are matched case-insensitively (stored lower-cased internally), and all state
lives in a static `Pipeline.Stores` dictionary (`Dictionary<string, List<Processor>>`) for the
lifetime of the PowerShell session/runspace — nothing here is persisted to disk on its own.

## Registration: folder → pipeline, file → processor

`Register-Pipeline -BasePath <dir> -Force` walks `<dir>` one level deep:

- Each **subfolder** becomes a pipeline, named after the folder, lower-cased
  (`Pipelines/Sitecore/` → pipeline `sitecore`).
- Each **file** inside that folder becomes one `Processor`, in `Directory.GetFiles(...).OrderBy(x
  => x)` order — i.e. plain alphabetical sort on the full path. This is why every shipped pipeline
  numbers its scripts (`00-Help.ps1`, `01-Resolve-Configuration.ps1`, `02-...`): the numeric prefix
  is the only thing controlling execution order, not the filename after it.
- A filename containing the literal substring `AlwaysRun` sets that processor's `AlwaysRun = true`
  (see `Aborted`/short-circuit below).
- `-Predecessors <name[]>` (pipeline names, or literal `Start-Pipeline ...` command strings) is
  stored on every processor registered in that call, and re-applied every time `Start-Pipeline`
  runs that pipeline.
- Without `-Force`, an already-registered pipeline name is left alone (its existing processor list
  is reused) — `-Force` is what makes a re-`Register-Pipeline` call rebuild it from disk.

`Processor` (the object type flowing through `Get-Pipeline`/`Update-Pipeline`):

```csharp
class Processor {
    bool     AlwaysRun;            // runs even if $arguments["Aborted"] -eq $true
    string   Path;                 // the .ps1 file, or a command name
    string   Pipeline;             // owning pipeline name — Update-Pipeline uses this to find it
    string[] PipelinePredecessors; // predecessor pipelines/commands set at registration
}
```

## Execution: `Start-Pipeline`

```powershell
Start-Pipeline sitecore @{ PublishUrl = "C:\Custom\Path" } -Verbose
```

1. Looks up the pipeline (throws `Pipeline <Name> is not registered` if it isn't).
2. Unions any explicit `-Predecessors` with every processor's stored `PipelinePredecessors`, then
   runs each predecessor **before** this pipeline's own processors: a literal `Start-Pipeline ...`
   string is invoked as-is; anything else is treated as a pipeline name and started recursively
   (`Start-Pipeline $name $Args -Verbose:$verbose`) — same shared `$Args` hashtable passed through.
3. If `-Help` was passed, `Args["Help"] = $true` is set before any processor runs.
4. Iterates processors in registration order. For each one:
   - Skipped (with a verbose message only) if `Args["Aborted"] -eq $true` **and** the processor is
     not `AlwaysRun`.
   - Otherwise invoked with the shared hashtable: a `*.ps1` path is **dot-sourced**
     (`. $psCommand $psArgs`), so it runs in the caller's scope and can mutate `$arguments` in
     place; anything else is called normally (`& $psCommand $psArgs`).

Every shipped processor follows the same shape — `param([hashtable]$arguments)` — and treats
`$arguments` as shared, mutable state across the whole pipeline (and across predecessor pipelines,
since the same hashtable is threaded through). Typical uses seen throughout `Pipelines/`:
resolving `SolutionPath`/`Configuration` once and having every later step read it back,
`Get-GitChanges`-style diffing into `Args["Changes"]` for a later archive/migration step to
consume, or OS-gating a step (`Install/03-Linux-Install.ps1` returns immediately if
`-not $IsLinux`).

### The `Help` / `Aborted` short-circuit convention

Every shipped pipeline's first processor is `00-Help.ps1`:

```powershell
param([hashtable]$arguments)
if ($arguments.ContainsKey("Help")) {
    Write-Host "Usage : ..." -ForegroundColor Yellow
    $arguments["Aborted"] = $true   # every later non-AlwaysRun processor is skipped
}
```

So `Start-Pipeline sif -Help` prints usage and stops there, while `Start-Pipeline sif @{ Solr =
$true }` (no `Help` key) runs the real steps. Reuse this pattern for your own pipelines: an
early processor that can set `Aborted` is the idiomatic "stop the rest of this pipeline" hook —
prefer it over throwing, since `AlwaysRun`-flagged cleanup/logging steps still execute.

## Shipped pipelines (all under `Pipelines/`)

| Pipeline | What its processors do |
|---|---|
| `startup` | Bootstraps a session: `Set-TrustPolicy`/Chocolatey profile import, discovers `*.sln`-adjacent projects, generates/invokes EF Core migrations (`New-Migration`, `Invoke-Migration`). |
| `artifact` | Resolves `sharpps.config`/`SolutionPath`, diffs git changes, builds artifact-migration scripts, archives `inetpub`/`database`/`packages`/`documentation` into a deployable artifact. |
| `publish` | Resolves solution + build `Configuration`/`SolutionTargets` (default `Debug`, `restore`+`rebuild`), then publishes selected `Folders` to a target path. |
| `install` | Cross-platform bootstrap: Chocolatey on Windows, native package managers on Linux/macOS, plus a `sharpps-traefik` release-download step. |
| `sif` | Sitecore Install Framework wrapper: prerequisites, cert creation, package downloader, Solr install, CM/CD install (with SXA variants). |
| `sitecore` | Orchestrates a full deploy: publish → DB migration → warm-up (`Start-SiteUp`) → Unicorn sync (`Invoke-SyncUnicorn`). |
| `traefik` | Local reverse-proxy management: resolve `traefik.yml` config, toggle API debug, tail logs, add/edit a dynamic service YAML. |

Run `Start-Pipeline <name> -Help` to print any of these pipelines' own usage/arguments banner
rather than relying on this table for exact argument names — the `00-Help.ps1` script is the
source of truth and is kept next to the processors it documents.

## Inspecting a pipeline

```powershell
Get-Pipeline -Name sitecore
# Path                                    AlwaysRun Pipeline  PipelinePredecessors
# ----                                    --------- --------  --------------------
# ...\Pipelines\Sitecore\00-Help.ps1      False     sitecore  {}
# ...\Pipelines\Sitecore\01-Publish.ps1   False     sitecore  {}
# ...
```

## Patching a pipeline at runtime: `Update-Pipeline`

`Update-Pipeline` is how you reshape an **already-registered** pipeline for the rest of the
session without touching the module's shipped `.ps1` files — swap a step's implementation, splice
a new step next to an existing one, reorder, or drop a step. Always start from a `Processor`
object obtained via `Get-Pipeline` on the *same* pipeline you're about to mutate — `Update-Pipeline`
looks the pipeline up by `Processor.Pipeline`, and finds the target's position with
`pipeline.IndexOf(Processor)`, so the object must be the actual list member (or an `Equals`-equal
one), not a hand-built lookalike.

```powershell
$publishStep = Get-Pipeline sitecore | Where-Object Path -like "*01-Publish*"
```

**Replace** — swap the script a step runs, keep its position:
```powershell
Update-Pipeline -Processor $publishStep -Path "C:\custom\01-Publish.ps1" -Action Replace
```

**InsertBefore / InsertAfter** — splice a brand-new processor next to an existing one (e.g. a
pre-flight check before `Publish`, or a notification step right after it):
```powershell
Update-Pipeline -Processor $publishStep -Path "C:\custom\00b-PreflightCheck.ps1" -Action InsertBefore
Update-Pipeline -Processor $publishStep -Path "C:\custom\01b-NotifySlack.ps1"    -Action InsertAfter
```

**MoveTo** — reorder a step without changing what it runs (index is 0-based; the cmdlet adjusts
for the removal shift internally, so pass the *target* index in the pipeline as it exists today):
```powershell
Update-Pipeline -Processor $publishStep -MoveTo 0
```

**Remove** — drop a step entirely:
```powershell
Update-Pipeline -Processor $publishStep -Remove
```

Notes:
- `-Action` and `-Path` (Replace/InsertBefore/InsertAfter), `-MoveTo`, and `-Remove` are mutually
  exclusive concerns handled independently in the cmdlet — don't combine `-MoveTo` with `-Action`
  in one call; do them as separate calls if you need both.
- A patch only lives in the current `Pipeline.Stores` — a new PowerShell process re-imports the
  module fresh and only sees what `Register-Pipeline` finds on disk again. To make a change
  durable, either drop your own numbered `.ps1` into the real `Pipelines/<name>/` folder (or your
  own custom folder — see below) and re-run `Register-Pipeline -BasePath <dir> -Force`, or re-run
  the same `Update-Pipeline` calls (e.g. from your own profile/init script) every session.
- Filenames still matter after a patch: a path containing `AlwaysRun` sets `AlwaysRun = true` on
  a `Replace`/insert exactly like at registration time (same substring check), so name custom
  steps accordingly if they must survive an `Aborted` short-circuit.

## Adding your own pipeline

You don't have to patch a shipped one — register an entirely new pipeline from your own folder,
using the same folder-per-pipeline / numbered-file-per-processor convention:

```powershell
# MyTools/Pipelines/deploy-prod/00-Help.ps1
# MyTools/Pipelines/deploy-prod/01-Build.ps1
# MyTools/Pipelines/deploy-prod/02-Deploy.ps1
Register-Pipeline -BasePath "MyTools/Pipelines" -Predecessors startup -Force
Start-Pipeline deploy-prod @{ }
```

`-Predecessors startup` means every `Start-Pipeline deploy-prod` run first runs the `startup`
pipeline to completion (sharing the same `$Args`) before `deploy-prod`'s own processors execute —
the same mechanism the shipped pipelines could use to depend on each other, chained arbitrarily
deep since predecessor resolution recurses.
