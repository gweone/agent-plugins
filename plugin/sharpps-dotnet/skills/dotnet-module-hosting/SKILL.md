---
name: dotnet-module-hosting
description: Host SharpPS ASP.NET Core feature modules with AspNetHosting.Main, SharpPS.AspNetCore, FeatureBuilderService, packages discovery, feature manifests, hostname filtering, and AssemblyLoadContext. Use for host-versus-feature bootstrap, MVC/Razor parts, layered JSON configuration, startup pipelines, static assets, and the Administrations example.
---

# .NET modular ASP.NET Core hosting

Use for Pattern 4: independently built features loaded into one host process.
A single-assembly app does not need plugin-directory/load-context machinery.

## Checklist

1. Consume `SharpPS.AspNetCore` in the host. Its inspected package targets
   `net8.0`/`net9.0`/`net10.0`; verify the consuming project's resolved version.
2. Keep host `Program.cs` at `await AspNetHosting.Main(args);`. Bootstrap wires
   `AddSharpPipeline()` and `AddSharpPSAspnetCore()` once per runtime server.
3. Let `IFeatureBuilder` discover `<AppBase>/packages/*`, optional
   `*.feature.json` manifests, and hostname-allowed feature assemblies through
   `FeatureAssemblyLoadContext`; `Feature:BuilderPartName` can select a builder.
4. Layer feature JSON configuration, then register MVC application parts,
   Razor runtime compilation, and assembly service configurators. Include the
   host entry assembly, not only loaded features.
5. Feature modules contribute `IServiceConfiguration`, controllers, options,
   manual registrations, and `AddSharpPipelineConfigurator` calls. They do not
   repeat host bootstrap or call the host's per-assembly discovery APIs.
6. After app build, run the `InitializeRequestArgs` pipeline in
   `Scopes.Default.AspnetCore`, combine feature/host `wwwroot` providers, and
   map default/area MVC routes from `FeatureConfiguration.DefaultRoute`.

## Focused lookup

- [Bootstrap sequence and host-versus-feature roles](references/bootstrap-and-administrations.md#bootstrap-sequence-and-host-versus-feature-roles).
- [RuntimeServer, feature loading, MVC/Razor, config, and static-asset source trace](references/bootstrap-and-administrations.md#source-trace).
- [Administrations project, config, DI, ReplaceWith, Swagger, and variance example](references/bootstrap-and-administrations.md#what-a-standard-project-actually-looks-like-end-to-end).
- [Package references, target snapshot, and evidence boundaries](../dotnet-service-registration/references/packages-and-evidence.md).

## Boundaries

- Consume bootstrap/loader packages; do not copy core internals into modules.
- An isolated `AssemblyLoadContext` is not a security sandbox or a guarantee
  of hot unloading. Domain filtering is the traced module-selection behavior.
- The Administrations source example has its own host entry point; a feature
  loaded inside another host does not invoke that entry point again.
- Source paths identify historical external examples, not plugin files or
  newly tested APIs. This is not a build/deployment or generic hosting guide.

## Related skills

- [dotnet-service-registration](../dotnet-service-registration/SKILL.md) — per-module DI configurators.
- [dotnet-processor-pipelines](../dotnet-processor-pipelines/SKILL.md) — C# scoped processors/patches.
- [dotnet-storage-providers](../dotnet-storage-providers/SKILL.md) — named backend registration.
