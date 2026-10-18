# Registration and execution

These are external source/version examples, not newly verified runtime behavior. Inspect the
installed module's source before execution; registration changes the session and scripts may
perform deployments, migrations, archives, or software installation. Require an explicit target,
arguments, predecessor graph, and authorization under **Spec → Plan → Execution**.

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
  => x)` order — i.e. plain alphabetical sort on the full path. This is why the documented pipelines
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
3. Only **after predecessors complete**, if `-Help` was passed, `Args["Help"] = $true` is
   set before this pipeline's own processors run. Predecessors do not automatically receive
   the outer `-Help` switch, although an existing `Help` key is shared with them.
4. Iterates processors in registration order. For each one:
   - Skipped (with a verbose message only) if `Args["Aborted"] -eq $true` **and** the processor is
     not `AlwaysRun`.
   - Otherwise invoked with the shared hashtable: a `*.ps1` path is **dot-sourced**
     (`. $psCommand $psArgs`), so it runs in the caller's scope and can mutate `$arguments` in
     place; anything else is called normally (`& $psCommand $psArgs`).

Processors in the documented source follow the same shape — `param([hashtable]$arguments)` — and treats
`$arguments` as shared, mutable state across the whole pipeline (and across predecessor pipelines,
since the same hashtable is threaded through). Typical uses seen throughout `Pipelines/`:
resolving `SolutionPath`/`Configuration` once and having every later step read it back,
`Get-GitChanges`-style diffing into `Args["Changes"]` for a later archive/migration step to
consume, or OS-gating a step (`Install/03-Linux-Install.ps1` returns immediately if
`-not $IsLinux`).

### The `Help` / `Aborted` short-circuit convention

The documented pipelines use `00-Help.ps1` as the first processor; verify the installed list:

```powershell
param([hashtable]$arguments)
if ($arguments.ContainsKey("Help")) {
    Write-Host "Usage : ..." -ForegroundColor Yellow
    $arguments["Aborted"] = $true   # later non-AlwaysRun processors are skipped; AlwaysRun may still run
}
```

`Start-Pipeline sif -Help` is intended to print usage and abort ordinary subsequent steps;
`Start-Pipeline sif @{ Solr = $true }` (no `Help` key) requests the real steps. This is a
**processor convention, not an engine dry-run or read-only guarantee**: predecessors run before
the engine sets `Help`, earlier/custom processors can do work, and `AlwaysRun` steps still run
after abort. Prefer `Get-Pipeline` and reading `00-Help.ps1`/predecessor source for inspection.
An early `Aborted` flag is the idiomatic stop hook; unlike throwing, it leaves eligible
`AlwaysRun` cleanup/logging steps in the execution loop. Audit their side effects too.

## Inspecting a pipeline

```powershell
Get-Pipeline -Name sitecore
# Path                                    AlwaysRun Pipeline  PipelinePredecessors
# ----                                    --------- --------  --------------------
# ...\Pipelines\Sitecore\00-Help.ps1      False     sitecore  {}
# ...\Pipelines\Sitecore\01-Publish.ps1   False     sitecore  {}
# ...
```

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

## Source and lookup map

Source traces: `RegisterPipelineCommand`, `StartPipelineCommand`, `GetPipelineCommand`,
`UpdatePipelineCommand`, `Pipeline.Stores`, `Processor`, and the installed `Pipelines/` scripts
in `SharpPS.Shells` (symbol/file spelling can vary by version). Literal predecessor command
strings are executable code: review them, not just pipeline names. Recursion requires inspecting
the full dependency graph; avoid cycles and do not assume the main pipeline owns all effects.

- [Runtime patching](../../sharpps-pipeline-patching/references/runtime-patching.md) for object identity and action calls.
- [Module setup](module-setup.md) for host/import and trust boundaries.
- [Version-scoped catalog](shipped-pipelines.md) for examples, not an installed inventory.
- [Runtime entrypoint](../SKILL.md).
