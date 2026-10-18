---
name: sharpps-pipeline
description: Inspect, register, and run SharpPS.Shells PowerShell pipelines with Get-Pipeline, Register-Pipeline, and Start-Pipeline. For runtime Update-Pipeline changes use sharpps-pipeline-patching.
---

# SharpPS.Shells pipeline lookup

PowerShell **SharpPS.Shells**, not the C# `SharpPS.Pipeline` library or Sitecore
`CorePipeline`. A named pipeline is an ordered processor list sharing one mutable `$Args`
hashtable. This is an operational engine, not read-only orchestration metadata.

## Spec → Plan → Execution

1. **Spec** — distinguish inspection, module setup, registration, execution, and runtime
   patching. Resolve the host/session, pipeline, explicit target, full arguments, predecessors,
   and authorization. Ask rather than guess. Deployment, DB migration, archiving, software
   installation, trust policy changes, and container operations have real side effects.
2. **Plan** — state the exact cmdlet, PowerShell host, pipeline, full argument hashtable,
   predecessor graph, and expected effects before running it. Obtain explicit authorization
   for operational targets and effects; source examples are not permission to execute.
3. **Execution** — perform only the authorized plan. Report processors/effects, output, and
   how `Aborted`/`Help` affected execution, including any `AlwaysRun` activity.

Never automatically install a host/module, trust a repository, or bypass certificates.
Import runs initialization; see [module setup](references/module-setup.md) before changing it.

## Inspect before running

```powershell
Get-Pipeline -Name sitecore
```

Prefer this and installed processor/source inspection, including `00-Help.ps1`, over executing
Help. **`Start-Pipeline -Help` is not universally safe/read-only:** the engine executes
predecessors before setting `Help`; `AlwaysRun` may execute after `Aborted`. Help is only an
intended processor convention. Review the entire chain before authorizing even a Help request.

## Focused lookup

| Need | Read |
|---|---|
| Host, import, gallery, installation/trust boundaries | [Module setup](references/module-setup.md) |
| Cmdlets, registration, shared Args, execution order, inspection, minimal custom example | [Registration and execution](references/registration-and-execution.md) |
| `artifact`, `install`, `publish`, `sif`, `sitecore`, `startup`, `traefik` | [Version-scoped catalog](references/shipped-pipelines.md) |
| Replace/insert/move/remove a live Processor | [Runtime patching skill](../sharpps-pipeline-patching/SKILL.md) |
| Create persistent workspace processors/configuration | [Authoring skill](../sharpps-pipeline-authoring/SKILL.md) |

## Evidence boundary

References preserve external source/version examples; they were **not newly runtime-verified**.
Inspect the installed module/version rather than assuming this catalog is exhaustive or current.
In particular, `deploy`/`docker` authoring examples are not guaranteed shipped pipelines.
Registration and patches live in session `Pipeline.Stores`; persistent file changes are separate
operations. `-Force` registration rebuilds lists and can replace previously patched state.
