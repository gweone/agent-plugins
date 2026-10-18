# Pattern 4 — Composition-root host bootstrap with plugin-style module loading

## Evidence and package boundary

The source traces and worked example below are preserved from the historical external
SharpPS consuming solution. They are not files in this plugin or newly tested APIs.
Framework targets/package wiring describe that snapshot; confirm the consuming project's
resolved versions. Use `SharpPS.AspNetCore` rather than copying bootstrap/loader internals.
See [package roles and evidence scope](../../dotnet-service-registration/references/packages-and-evidence.md).

Pattern 1 here means [service registration](../../dotnet-service-registration/SKILL.md);
Pattern 3 means the [C# SharpPS.Pipeline engine](../../dotnet-processor-pipelines/SKILL.md).

## Problem and fit

Hosting several independently-built feature assemblies ("plugins") in one ASP.NET
Core process, where each plugin needs both its DI services (Pattern 1) and its MVC controllers
registered, optionally serving a different feature set per hostname, without the host's
`Program.cs` ever needing to know any plugin's name or reference its assembly at compile time.

Use for multiple independently-built/deployed feature modules in one process (a genuine
plugin architecture), especially when different modules should be servable on different
hostnames from a single deployment. A single-assembly ASP.NET Core app just needs DI/pipeline
bootstrap calls directly in a normal `Program.cs`/`Startup`, without a plugin-directory scan
or isolated load context.

## Bootstrap sequence and host-versus-feature roles

1. The host's entire entry point is one call into a shared bootstrap function — nothing else in
   `Program.cs`. That function builds the web app, wires the two DI/pipeline patterns above once,
   and hands everything else to a swappable plugin-loading strategy.
2. That strategy scans a well-known plugin directory (one subfolder per feature), optionally reads
   a small manifest per feature (name, and which hostnames it's allowed to serve — enabling
   multi-tenant hosting from one deployment), and loads each allowed feature's assembly through an
   **isolated** `AssemblyLoadContext` rather than a plain `Assembly.Load`.
3. For every loaded feature assembly — and separately for the host's own entry assembly — the
   bootstrap does exactly two things: registers its controllers as an MVC application part (with
   Razor runtime compilation against that assembly's embedded views), and runs Pattern 1's
   auto-discovery (`ConfigureServices(assembly)`) against it. A feature module itself never calls
   either registration API — it just ships an `IServiceConfiguration` implementor and some
   controllers, and the host's bootstrap finds both.
4. Per-feature JSON config files found in each feature's folder are layered into the host's
   `IConfiguration` before any of that runs, so a feature can ship its own settings file instead of
   editing the host's config.
5. At app-build time (after `WebApplication.Build()`), the bootstrap runs an initialization step
   through Pattern 3's pipeline engine under a well-known scope — giving every loaded feature a hook
   to plug startup logic in via `AddSharpPipelineConfigurator` without editing the host — then
   merges every feature's static-asset folder (plus the host's own) into one composite file
   provider, and maps the routing conventions.

The custom load context is a loading strategy, not evidence of a security sandbox or hot
unloading. Feature modules do not call `AddSharpPSAspnetCore()`/`AddSharpPipeline()` themselves;
the host owns that bootstrap once.

## Source trace

Every host `Program.cs` in the inspected solution is just
`await AspNetHosting.Main(args);` (`SharpPS.AspNetCore.Api/Program.cs`,
`SharpPS.AspNetCore.Administrations/Program.cs`, `SharpPS.AspNetCore.Layouts/Program.cs`).
`AspNetHosting.Main` (`SharpPS.AspNetCore/SharpPS.AspNetCore/AspNetHosting.cs`) builds a
`RuntimeServer` per configured hosting URL; `RuntimeServer.Build`
(`SharpPS.AspNetCore/SharpPS.AspNetCore/Runtime/RuntimeServer.cs:39-48`) creates the
`WebApplicationBuilder` and calls `_builder.Services.AddSharpPipeline()` (Pattern 3's core) and
`AddSharpPSAspnetCore()` (MVC/JSON conventions plus a few built-in processors registered under
`Scopes.Default.AspnetCore`, `SharpPS.AspNetCore/SharpPS.AspNetCore/ServiceCollectionExtensions.cs:30-65`),
then resolves an `IFeatureBuilder` — either dynamically loaded from a `Feature:BuilderPartName`
config key, or the default `FeatureBuilderService`
(`SharpPS.AspNetCore/SharpPS.AspNetCore/Parts/FeatureBuilderService.cs`). `FeatureBuilderService.Build`
scans `<AppBase>/packages/*`, reads an optional `*.feature.json` manifest per folder
(`FeaturePart.Domains`/`IsAllowedFor(url)` for hostname filtering,
`SharpPS.AspNetCore/SharpPS.AspNetCore/Parts/FeaturePart.cs`), loads each allowed feature's
`<Name>.dll` via a custom `FeatureAssemblyLoadContext`, and for it (and the entry assembly) calls
`builder.Services.AddFeature(assembly)` (`AddApplicationPart` + Razor runtime compilation,
`ServiceCollectionExtensions.cs:66-72`) and `container.ConfigureServices(assembly)` — an instance of
`SharpPS.DependencyInjection.ServiceContainer`, the class that actually invokes Pattern 1's
per-assembly `IServiceConfiguration` scan. `FeatureBuilderService.Initialize` then runs an
`InitializeRequestArgs` pipeline through `IPipeline<,>.Run(args, Scopes.Default.AspnetCore)`, wires
a `CompositeFileProvider` over every feature's `wwwroot`, and maps the default + area MVC routes
from `FeatureConfiguration.DefaultRoute`.

## What a standard project actually looks like, end to end

`SharpPS.AspNetCore.Administrations` is the inspected complete instance of these patterns wired
together — a source example for an ASP.NET Core host/module in that solution:

- **`.csproj`**: `Sdk="Microsoft.NET.Sdk.Web"`, multi-targets `net8.0;net9.0;net10.0`, packable
  (`GeneratePackageOnBuild`/`IsPackable`), and pulls in the bootstrap with a single
  `<ProjectReference Include="..\SharpPS.AspNetCore\SharpPS.AspNetCore.csproj" />` — it does
  **not** reference `SharpPS.DependencyInjection`/`SharpPS.Pipeline` directly; those come
  transitively through `SharpPS.AspNetCore`
  (`SharpPS.AspNetCore/SharpPS.AspNetCore.Administrations/SharpPS.AspNetCore.Administrations.csproj`).
  Anything the module itself needs beyond that (here, `Swashbuckle.AspNetCore` for Swagger) is just
  an ordinary extra `<PackageReference>`.
- **`Program.cs`**: exactly `await AspNetHosting.Main(args);` — identical across every inspected host project,
  confirming Pattern 4's bootstrap call is the whole entry point there.
- **`api.config.json`** at the project root: the per-module JSON settings file Pattern 4's
  `FeatureBuilderService.Build` auto-layers into `IConfiguration` (it also applies to the host's
  own entry assembly, not only loaded plugins — `AppContext.BaseDirectory` is unioned into the
  scanned paths).
- **`DependencyInjection/ServiceConfiguration.cs`**: `IServiceConfiguration.Configure` here does
  three things in order — (1) Pattern 1's
  `services.RegisterServices(this.GetType().Assembly)` first; (2) ordinary hand-written ASP.NET
  Core wiring specific to this module (`AddAuthorization`, `AddEndpointsApiExplorer`,
  `AddSwaggerGen(...)` reading its own `configuration.GetSection("Api")`) — so `Configure` is not
  *only* the auto-discovery call, it's also where a module does whatever manual service
  registration it needs; (3) Pattern 3 registration for this module's own pipeline steps:
  `services.AddSharpPipelineConfigurator<AdministrationInitialize, InitializeRequestArgs>((x, c) => x.ReplaceWith(x => x.Configurator.ProcessorType == typeof(VariantProcessor), c), Scopes.Default.AspnetCore)`
  followed by `services.AddSharpPipelineConfigurator<VariantProcessor, InitializeRequestArgs>(Scopes.Default.AspnetCore)`
  — the preserved use of the `ReplaceWith` patch operation.
- **`Pipelines/Initialize/AdministrationInitialize.cs`** (`IProcessor<InitializeRequestArgs>`) is
  this module's hook into the startup pipeline (the final bootstrap step above): it calls
  `args.Application.UseSwagger()` and maps a Swagger UI under this module's own area path — this is
  *how* a loaded module adds middleware/endpoints during startup without the host needing to know
  about it. **`Pipelines/Initialize/VariantProcessor.cs`** (`IProcessor<RequestArgs>`) shows the
  contravariance point in practice: it's registered against `InitializeRequestArgs` even
  though it's written against the base `RequestArgs`, and reads `args.RequestServices` to resolve
  an `ILogger<T>` from the ambient scope.
