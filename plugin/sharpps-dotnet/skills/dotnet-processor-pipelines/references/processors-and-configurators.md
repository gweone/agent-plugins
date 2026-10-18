# Pattern 3 — Lightweight processor pipeline

## Evidence and engine boundary

This is the C# `SharpPS.Pipeline` package's `IProcessor<TArgs>` + configurator mechanism.
Source paths and line numbers below refer to the historical external SharpPS solution,
not plugin files or newly tested APIs. Consume the package rather than copying its internals;
see [package roles and evidence scope](../../dotnet-service-registration/references/packages-and-evidence.md).

This is not the PowerShell `SharpPS.Shells` JSON/job engine
([sharpps-pipeline](../../sharpps-pipeline/SKILL.md),
[sharpps-pipeline-authoring](../../sharpps-pipeline-authoring/SKILL.md)), nor Sitecore's native
XML-configured `CorePipeline`. Sitecore XML processors are not registered through
`AddSharpPipelineConfigurator` or its DI collection patches.
A project embedded in Sitecore may legitimately use both C# engines; choose per call site.

## Problem and fit

A cross-cutting flow (request handling, a multi-step build/transform) needs an
ordered, independently-extensible sequence of steps, but a full mediator or behavior-pipeline
library is more machinery than the problem needs — steps are added by different modules and must
be reorderable without editing a shared list.

Use when the step sequence is genuinely cross-cutting and contributed to by multiple modules,
and needs reordering/insertion without editing existing step code. A fixed, single-module
sequence is just a method calling other methods in order.

## Processor contract and collection patches

1. `IProcessor<in TArgs>` — one step: a required `bool AlwaysRun` (run even if an earlier step
   aborted the pipeline) and one `void Process(TArgs args)` method. `TArgs` is contravariant, so a
   processor written against a base args type can register for any pipeline whose args type
   derives from it (e.g. a processor over the base `RequestArgs` can serve a pipeline scoped to
   the more specific `InitializeRequestArgs : RequestArgs`).
2. `IPipelineConfigurator` — registered once per (processor, args, scope) triple; besides adding
   the processor to DI, it can carry an optional `patch` delegate that edits the already-built
   `ProcessorCollection<TArgs, TScope>` before it runs — named operations: `MoveTo(index, ...)`,
   `MoveBefore(predicate, ...)`, `MoveAfter(predicate, ...)`, `ReplaceWith(predicate, ...)`,
   `Remove(...)`/`Remove(predicate)` — so a later-loaded module can reorder, substitute, or drop a
   step from an earlier module without editing that module's code.
3. A small core (`IPipeline<,>`, `IPipelineManager`) resolves all registered configurators for a
   given scope, builds the ordered processor collection (applying patches), and runs it.
4. Registration is one extension call per processor: `services.AddSharpPipelineConfigurator<TProcessor, TArgs>(patch, scope)`,
   with a one-time `services.AddSharpPipeline()` to wire the core machinery.

`AlwaysRun` describes the abort behavior above; it is not evidence of exception-recovery,
retry/resilience, or asynchronous processor APIs. Do not infer such APIs from the package name.

## Registration source trace

`SharpPS.Pipeline/SharpPS.Pipeline/DependencyInjection/PipelineServiceCollectionExtensions.cs` —
`AddSharpPipeline()` wires `IPipeline<,>`/`IPipelineScope<,>`/`IPipelineManager`;
`AddSharpPipelineConfigurator<TProcessor, TArgs>(patch, scope)` registers one processor plus its
optional collection-patch delegate. Used by ASP.NET Core projects for cross-cutting request
pipelines (e.g. `SharpPS.AspNetCore.Api`'s `ServiceConfiguration`).

In the modular host, the host bootstrap calls `AddSharpPipeline()` once; feature modules
contribute configurators, not another core bootstrap. See
[dotnet-module-hosting](../../dotnet-module-hosting/SKILL.md) and its
[Administrations example](../../dotnet-module-hosting/references/bootstrap-and-administrations.md#what-a-standard-project-actually-looks-like-end-to-end)
for the preserved `ReplaceWith` expression, startup hook, and base-args variance example.
