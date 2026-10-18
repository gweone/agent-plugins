---
name: dotnet-service-patterns
description: Select among four SharpPS .NET modular-solution patterns — marker-interface DI registration, named storage providers, C# processor pipelines, and ASP.NET Core module hosting. Use when choosing a service architecture or when the feature-specific pattern is not yet clear.
---

# Four .NET patterns for modular solutions

Use this selector to choose among four SharpPS package-backed patterns.
For a known task, go directly to its focused skill. This is not a general HTTP,
resilience, hosted-service, background-processing, or production-service guide.

## Pattern 1 — Convention-based service auto-registration (marker-interface scanning)

Use [dotnet-service-registration](../dotnet-service-registration/SKILL.md) for
`IService` lifetime markers, `RegisterServices(assembly)`, and per-module
`IServiceConfiguration`. Sitecore's own configurator contract remains separate.

## Pattern 2 — Pluggable provider with a fluent registration builder

Use [dotnet-storage-providers](../dotnet-storage-providers/SKILL.md) for named
`IStorageProvider<T>` implementations, `IOptionsMonitor`, `AddStorage`, backend
`Use<X>Storage` extensions, and the limited per-module EF Core example.

## Pattern 3 — Lightweight processor pipeline

Use [dotnet-processor-pipelines](../dotnet-processor-pipelines/SKILL.md) for C#
`SharpPS.Pipeline`: `IProcessor<in TArgs>`, `AlwaysRun`, scoped configurators,
collection patch ordering, and one-time core registration.

## Pattern 4 — Composition-root host bootstrap with plugin-style module loading

Use [dotnet-module-hosting](../dotnet-module-hosting/SKILL.md) for
`SharpPS.AspNetCore`, `AspNetHosting.Main`, feature assembly/config discovery,
MVC/Razor/static assets, and the Administrations worked example.

## Package and evidence boundaries

- Consume NuGet packages; do not copy scanner/builder/pipeline internals.
- Host bootstrap and feature contributions have different responsibilities.
- [Package roles, snapshot targets, historical source paths, and non-patterns](../dotnet-service-registration/references/packages-and-evidence.md).
  External source traces are not plugin files or newly tested APIs.

## Other pipeline engines

- [sharpps-pipeline](../sharpps-pipeline/SKILL.md) — PowerShell `SharpPS.Shells` JSON jobs.
- Sitecore's XML `CorePipeline` is separate from the C# package engine; its processors are registered in Sitecore XML, not through `AddSharpPipelineConfigurator`.
