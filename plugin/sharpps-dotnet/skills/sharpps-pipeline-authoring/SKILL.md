---
name: sharpps-pipeline-authoring
description: Create SharpPS.Shells workspace pipelines and PowerShell processors. Covers pipeline versus function, shared arguments, sharpps.config, Help/Aborted/AlwaysRun, chaining, and verification.
---

# Authoring SharpPS.Shells workspace pipelines

For PowerShell **SharpPS.Shells**, not C# `SharpPS.Pipeline` or Sitecore `CorePipeline`.
For running/inspection use [runtime lookup](../sharpps-pipeline/SKILL.md); for session mutations
use [runtime patching](../sharpps-pipeline-patching/SKILL.md). Authoring changes persistent files.

## Spec → Plan → Execution

1. **Spec** — agree capability, workspace/file targets, trigger keys, configuration, failure
   behavior, and verification fixtures. Choose a function or a real multi-step pipeline below.
2. **Plan** — name exact files and intended ordering, shared-state keys, and tests. Execution
   requires a separately explicit host/session, full arguments, predecessor graph, target, and
   authorization for deployments, migrations, installs, container operations, or other effects.
3. **Execution** — edit only agreed files; run only authorized isolated checks and report gaps.
   Never automatically install/trust/bypass certificates or use a real unrequested target.

## Rule 0 — pipeline or public function?

- One capability belongs in `Functions/Verb-Noun.ps1`: composable parameters, tab completion,
  and `-WhatIf` where implemented. Never add a pipeline merely translating a hashtable into
  one function's parameters. Processors orchestrate public functions; functions do the work.
- A pipeline is an ordered sequence with shared state and abort semantics: later steps depend
  on earlier results. Do not wrap a single obvious command (`docker logs`, `docker exec ...
  bench`); wrap meaningful sequences, non-obvious incantations, parsing, hashing, or polling.

## Rule 1 — stack-neutral and machine-neutral

No machine-specific absolute paths, even defaults; no stack-specific module defaults.
Project settings belong in lowercase XML `sharpps.config`; machine settings in environment
variables; per-call parameters/`$arguments` win. Missing optional config skips gracefully with
an exact key named in the message; required-operation failure warns, sets `Aborted`, and returns.

## Processor contract and Help safety

Numbered files share one mutable `[hashtable]$arguments`, including chained pipelines.
`Aborted` skips later non-`AlwaysRun` processors; cleanup/reporting may still execute.
`00-Help.ps1` intends to print usage and abort ordinary later steps, **not guarantee read-only
execution**: predecessors run before the engine sets `Help`, and `AlwaysRun` can run afterward.
Prefer reading source/`Get-Pipeline`; inspect all side effects before executing a Help check.

## Focused lookup

| Need | Read |
|---|---|
| Workspace tree, registration, processor template, 00-Help/banner pitfalls | [Layout and processors](references/layout-and-processors.md) |
| 01-Resolve-Configuration, XML keys, aborts, native exit/error handling | [Configuration and failure](references/configuration-and-failure.md) |
| Delegation/predecessors, isolated verification, worked source traces | [Chaining and verification](references/chaining-and-verification.md) |

`Invoke-Expression` build configuration is executable trusted code, not safe data; read its
[caveat](references/configuration-and-failure.md#command-configuration-is-trusted-code) before reuse.
External source/version examples are not newly runtime-verified. `Deploy/` and `docker` are
workspace/version examples, not guaranteed shipped pipelines; inspect the installed version.
