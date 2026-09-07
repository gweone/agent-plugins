# sharpps-dotnet

.NET tooling knowledge for solutions built on the [SharpPS](https://github.com/gweone) framework.

## Skills

| Skill | Covers |
|---|---|
| `decompile-dll` | Decompiling a .NET Framework or .NET Core/5+ DLL/EXE back to C# source using the `ilspycmd` CLI, which runs on any OS with the .NET SDK/runtime installed (Windows, Linux, macOS) — a scriptable alternative to dotPeek/dnSpy's Windows-only GUI. Resolves/acquires the target assembly via `dotnet restore` + the NuGet cache into a dynamically-resolved `decompiler/<product>/<version>/` layout (never a hardcoded path — same convention as `sharpps-liferay`'s `liferay-portal-source`). Covers dumping to stdout or a compilable project, decompiling a single type, listing/extracting embedded resources (incl. BAML/XAML for WPF), and resolving dependency-assembly references. |
| `sharpps-pipeline` | The `SharpPS.Shells` PowerShell module: its `Register-Pipeline`/`Start-Pipeline`/`Get-Pipeline`/`Update-Pipeline` cmdlets, the `Pipelines/<name>/NN-*.ps1` registration convention, the shared-`$arguments`-hashtable execution model with `AlwaysRun`/`Aborted`/`Help` short-circuiting, the shipped `artifact`/`install`/`publish`/`sif`/`sitecore`/`startup`/`traefik` pipelines, and how to patch an already-registered pipeline at runtime (`Replace`/`InsertBefore`/`InsertAfter`/`MoveTo`/`Remove`) without editing the shipped scripts. |
| `sharpps-pipeline-authoring` | How to *write* a correct SharpPS.Shells pipeline in a workspace: the pipeline-vs-public-function decision rule (processors orchestrate, functions do the work — never wrap single commands), stack/machine-neutrality rules (`sharpps.config` per project, env vars per machine, no hardcoded paths), the `00-Help` and `01-Resolve-Configuration` standard processors, `Aborted`-not-throw failure semantics, native-command gotchas (`$LASTEXITCODE` reset, `$ErrorActionPreference = "Stop"` around `Invoke-Expression`), pipeline chaining, and the pre-ship verification checklist. |
| `dotnet-service-patterns` | Four general-purpose .NET patterns for a modular solution, each with a verified SharpPS reference implementation: convention-based service auto-registration (`SharpPS.DependencyInjection` — marker interfaces + one assembly-scanning entry point per module, instead of hand-written `AddFoo()`/`AddBar()` chains), the pluggable-provider pattern (`SharpPS.Storage` + per-backend packages — one shared interface + a fluent builder letting each backend register itself under a name), a lightweight processor-pipeline pattern (`SharpPS.Pipeline` — `IProcessor<TArgs>` + `IPipelineConfigurator`) for a cross-cutting step sequence too small to need a full mediator library, and a composition-root host bootstrap (`SharpPS.AspNetCore`'s `AspNetHosting.Main` — a one-line `Program.cs` that scans a plugin directory via an isolated `AssemblyLoadContext`, supports per-plugin hostname filtering, and auto-wires MVC application parts + DI auto-discovery per loaded module). The first three ship as their own NuGet packages rather than source to duplicate. For Sitecore's own native pipeline engine, see the `sharpps-sitecore` plugin's `sitecore-pipelines` skill instead. |

## Action skill workflow: Spec → Plan → Execution

Skills in this plugin that run real commands (not just reference knowledge) follow a standard
three-phase convention — never skip straight to running a command: **Spec** (resolve the
concrete target, asking the user if ambiguous), **Plan** (state the exact command(s) about to
run before running them), **Execution** (run them and report the result). See each skill's own
`SKILL.md` for how it applies this to that skill's specific commands.

## Source

This skill originates from a decompiler workspace's `.claude/skills` directory, built up
over real project work. This plugin packages the same skill for installation into any
repository via the Claude Code plugin system, independent of that original workspace.
