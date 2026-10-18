# Runtime patching: Update-Pipeline

Applies to the PowerShell **SharpPS.Shells** engine, not C# `SharpPS.Pipeline` or Sitecore
`CorePipeline`. External source/version examples below have not been newly runtime-verified.

**Spec → Plan → Execution:** identify session/host, pipeline, exact current Processor, custom
script path, action/index/predecessors, and expected resulting order. Obtain approval for the
mutation and separately for running any resulting deployment, migration, or install. A patch
changes the registered graph; it does not authorize executing it. Inspect scripts first.

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
  durable with separately authorized persistent file edits, place your own numbered `.ps1` in
  an agreed `Pipelines/<name>/` folder (prefer a [custom workspace](../../sharpps-pipeline-authoring/references/layout-and-processors.md))
  and re-run `Register-Pipeline -BasePath <dir> -Force`, or re-run
  the same `Update-Pipeline` calls (e.g. from your own profile/init script) every session.
- Filenames still matter after a patch: a path containing `AlwaysRun` sets `AlwaysRun = true` on
  a `Replace`/insert exactly like at registration time (same substring check), so name custom
  steps accordingly if they must survive an `Aborted` short-circuit.

## Inspect and verify without executing the pipeline

1. Use `Get-Pipeline` to inspect current members; select exactly one intended Processor.
   Resolve ambiguous or empty matches instead of passing them onward. Keep the real object,
   not a projection/reconstructed copy, and re-fetch after re-registration/replacement.
2. Review the custom script and its shared `$arguments` contract and predecessor effects.
3. Issue only the authorized patch calls, one action concern per call; re-query order, Path,
   AlwaysRun, Pipeline, and PipelinePredecessors to verify. Do not use `Start-Pipeline -Help`
   as a safety check: predecessors run before `Help` is set, and `AlwaysRun` may still run.
4. State that the change is session-only. Persistent changes require separately authorized
   edits to custom workspace processor files or an explicit session initialization mechanism;
   do not silently modify installed/shipped module files. Re-registration with `-Force` can
   replace the in-memory list and invalidate saved Processor objects.

All processors share `$Args`; `Aborted` skips only non-`AlwaysRun` members. A path containing
`AlwaysRun` can therefore introduce post-abort side effects, including on a Help request.

## Source traces and related lookup

- External `SharpPS.Shells` implementation: `UpdatePipelineCommand`, `Processor`,
  `Pipeline.Stores`, and `pipeline.IndexOf(Processor)` (inspect installed version).
- [Registration/execution and inspection](../../sharpps-pipeline/references/registration-and-execution.md).
- [Author persistent workspace processors](../../sharpps-pipeline-authoring/SKILL.md).
- [Patching entrypoint](../SKILL.md).
