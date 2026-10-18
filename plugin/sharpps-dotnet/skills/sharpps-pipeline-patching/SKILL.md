---
name: sharpps-pipeline-patching
description: Patch registered SharpPS.Shells PowerShell pipelines with Update-Pipeline Replace, InsertBefore, InsertAfter, MoveTo, or Remove. Covers Processor identity and session-only changes.
---

# Patch a registered SharpPS.Shells pipeline

PowerShell **SharpPS.Shells** only, not C# `SharpPS.Pipeline` or Sitecore `CorePipeline`.
This skill reshapes an already-registered pipeline in session memory, without editing shipped
processor files. For persistent workspace files use [authoring](../sharpps-pipeline-authoring/SKILL.md).

## Spec → Plan → Execution

1. **Spec** — identify host/session, pipeline, exact current Processor, custom script, desired
   action/index/predecessors, and expected order. Ask about ambiguous targets. Patching and
   running the resulting pipeline are separate operations requiring separate authorization.
2. **Plan** — state exact `Update-Pipeline` calls and anticipated changes. Review script and
   predecessor effects. Deployment, migration, installs, archives, and container actions require
   explicit targets/arguments and approval before any execution, not just approval to patch.
3. **Execution** — apply only authorized calls and inspect with `Get-Pipeline`; report resulting
   order, paths, flags, predecessors, and the session-only lifetime. Do not silently run it.

Never automatically install a host/module, trust a repository, or bypass certificates to patch.

## Identity and action rules

- Start with an actual `Processor` from `Get-Pipeline` on the same pipeline; select exactly one.
  `Processor.Pipeline` locates the list; `pipeline.IndexOf(Processor)` requires the actual member
  (or an Equals-equal object), not a hand-built lookalike or projected copy.
- Use separate calls for `-Action`/`-Path`, `-MoveTo`, and `-Remove`; do not combine concerns.
- `Replace`, `InsertBefore`, and `InsertAfter` use `-Path`; `MoveTo` uses a zero-based index.
  Paths containing `AlwaysRun` affect abort behavior on replacement/insertion.
- Re-query after changes. Re-registration with `-Force` may replace lists and invalidate saved
  objects. A new process imports disk state, not this session's patch history.

## Inspect, do not use Help as a dry-run

```powershell
Get-Pipeline -Name sitecore
```

Prefer registered graph and script/source inspection. The engine runs predecessors **before**
setting `Help`; `AlwaysRun` processors can still execute after `Aborted`. Thus
`Start-Pipeline -Help` is an intended usage convention, not universally safe/read-only execution.
Shared `$Args` flags flow across predecessor and processor calls; review the whole chain.

## Focused lookup

- [Runtime patching examples and source traces](references/runtime-patching.md): Replace,
  InsertBefore/After, MoveTo, Remove, object identity, and persistence choices.
- [Registration, execution order, and inspection](../sharpps-pipeline/references/registration-and-execution.md).
- [Module setup and trust boundaries](../sharpps-pipeline/references/module-setup.md).

Examples preserve external source/version guidance, **not newly verified runtime behavior**.
Persistent changes require separately authorized files or explicit session initialization;
never silently edit installed module scripts to make a runtime patch durable.
