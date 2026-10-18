---
name: dotnet-processor-pipelines
description: Build or patch C# SharpPS.Pipeline processor sequences with IProcessor<TArgs>, AlwaysRun, AddSharpPipelineConfigurator, scopes, MoveBefore, MoveAfter, ReplaceWith, and Remove. Use for DI-backed module-contributed processors, not PowerShell SharpPS.Shells JSON jobs or Sitecore CorePipeline XML.
---

# .NET C# processor pipelines

Use for Pattern 3: ordered cross-module steps that need extension or reordering.
For a fixed sequence inside one module, ordinary method calls are simpler.

## Checklist

1. Consume `SharpPS.Pipeline`; do not copy its registration/execution core.
2. Choose args and scope, then implement `IProcessor<in TArgs>` with
   `void Process(TArgs args)` and required `bool AlwaysRun`.
3. Set `AlwaysRun` for execution after an earlier abort; do not infer retry,
   exception-recovery, or async contracts from this behavior.
4. Register each (processor, args, scope) contribution through
   `services.AddSharpPipelineConfigurator<TProcessor, TArgs>(patch, scope)`.
5. Use collection patches to `MoveTo`, `MoveBefore`, `MoveAfter`, `ReplaceWith`,
   or `Remove` existing contributions instead of editing another module's code.
6. Register the core once with `services.AddSharpPipeline()`. In the modular
   ASP.NET Core host, bootstrap owns that call; features add configurators only.
7. Preserve contravariance: a base-args processor can serve a derived-args
   pipeline, as in `RequestArgs` versus `InitializeRequestArgs`.

## Focused lookup

- [Processor contract, abort behavior, variance, and collection patches](references/processors-and-configurators.md#processor-contract-and-collection-patches).
- [Core/configurator registration source trace](references/processors-and-configurators.md#registration-source-trace).
- [Administrations ReplaceWith, startup hook, and base-args example](../dotnet-module-hosting/references/bootstrap-and-administrations.md#what-a-standard-project-actually-looks-like-end-to-end).
- [Package roles and historical evidence scope](../dotnet-service-registration/references/packages-and-evidence.md).

## Engine boundaries

- This is the C# `SharpPS.Pipeline` DI engine, not the PowerShell
  `SharpPS.Shells` JSON/job engine and not Sitecore's XML `CorePipeline`.
- A Sitecore-hosted project may use both C# engines; choose explicitly per call
  site rather than treating DI patches as Sitecore XML processor registration.
- Historical source paths are consuming-repo examples, not plugin files or
  newly tested APIs; verify the project's resolved package version.

## Related skills

- [dotnet-module-hosting](../dotnet-module-hosting/SKILL.md) — initialization pipeline ownership.
- [dotnet-service-registration](../dotnet-service-registration/SKILL.md) — module DI configurators.
- [sharpps-pipeline](../sharpps-pipeline/SKILL.md) — PowerShell execution.
- [sharpps-pipeline-authoring](../sharpps-pipeline-authoring/SKILL.md) — PowerShell job authoring.
