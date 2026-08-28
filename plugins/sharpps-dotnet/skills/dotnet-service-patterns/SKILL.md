---
name: dotnet-service-patterns
description: Four general-purpose C#/.NET design patterns for a multi-project solution built from independently-shippable modules — convention-based service auto-registration (marker interfaces + assembly-scanning instead of hand-written `AddFoo()` chains), the pluggable-provider pattern (shared interface + fluent builder for named backend registration), a lightweight processor-pipeline pattern (`IProcessor<TArgs>` steps behind an `IPipelineConfigurator`), and a composition-root host bootstrap combining the first three into a plugin architecture (AssemblyLoadContext, per-plugin manifest, multi-tenant filtering). Each has a verified SharpPS reference implementation; the first three ship as NuGet packages (`SharpPS.DependencyInjection`, `SharpPS.Pipeline`, `SharpPS.Storage`). Use when designing service registration, adding a pluggable backend, or setting up an ASP.NET Core plugin host. Not the SharpPS.Shells PowerShell pipelines (`sharpps-pipeline`) or Sitecore's pipeline engine (`sharpps-sitecore`'s `sitecore-pipelines`).
---

# Four .NET patterns for modular solutions

A large .NET solution split into many independently-shipped projects (one per feature or backend)
tends to reinvent four problems: how does each project wire its own services into DI without a
central file that has to know about every project; how do you support several interchangeable
implementations of one capability (storage backend, auth provider, converter) without a giant
`switch`; how do you run an ordered, extensible sequence of steps without pulling in a full
mediator/pipeline framework; and how does a host process actually discover and load those
independently-built modules at runtime, instead of referencing every one of them by name at
compile time. The four patterns below are one working answer to each, each backed by a verified
reference implementation in the SharpPS solution (`SharpPS`, `SharpPS.Storage`, `SharpPS.Pipeline`,
`SharpPS.AspNetCore`, spanning .NET Framework and .NET Core/Standard).

## These patterns ship as NuGet packages, not just source to copy

Each pattern's core machinery is its own packable, versioned project (`GeneratePackageOnBuild`/
`IsPackable` set, no `<PackageId>` override so the package id is the project name) — consume it as
a `<PackageReference>`, don't re-implement the scanner/builder/pipeline core per project. Pattern 1
ships as the `SharpPS.DependencyInjection` package, Pattern 3 as `SharpPS.Pipeline`, and Pattern 2's
base (`IStorageProvider<T>`, `StorageProviderBuilder`) as `SharpPS.Storage`, with each storage
backend a separate package (`SharpPS.Storage.GoogleDrive`, `SharpPS.Storage.GoogleCloud`,
`SharpPS.Storage.EntityFramework`, ...) referenced only by the host that needs that backend.

`SharpPS.AspNetCore` (`SharpPS.AspNetCore/SharpPS.AspNetCore/SharpPS.AspNetCore.csproj`) is the
concrete evidence for this: it's a packable ASP.NET Core host-integration package (multi-targeting
`net8.0`/`net9.0`/`net10.0`) that itself references `SharpPS`, `SharpPS.DependencyInjection`, and
`SharpPS.Pipeline` as ordinary `<PackageReference>`s — the same packages a project author consumes
directly — alongside `Microsoft.AspNetCore.Mvc.Razor.RuntimeCompilation`. Don't copy
`SharpServiceCollectionExtensions`/`PipelineServiceCollectionExtensions` source into a new project;
reference the packages instead. Note the two roles are different, though: a **host** process
references `SharpPS.AspNetCore` and calls its bootstrap (Pattern 4 below); an ordinary **feature
module** hosted inside it only needs `SharpPS.DependencyInjection`/`SharpPS.Pipeline` directly (or
transitively) and never calls `AddSharpPSAspnetCore()`/`AddSharpPipeline()` itself — the host's
bootstrap wires those once for every module it loads.

## Pattern 1 — Convention-based service auto-registration (marker-interface scanning)

**Problem:** a solution with dozens of independently-shipped projects doesn't want one central
`Startup`/`Program` that hand-lists every service (`services.AddScoped<IFoo, Foo>(); ...`) from
every project — that file becomes a bottleneck and a merge-conflict magnet, and it's easy to ship
a new project without wiring it in at all.

**Shape of the pattern:**

1. Define a handful of empty marker interfaces distinguishing lifetime/registration shape —
   e.g. `IService` (transient), `IServiceScoped`, `IServiceSingleton`, plus `IServiceEnumerable`
   for types that should be added with `TryAddEnumerable` (multiple implementations of the same
   interface expected to coexist) and `IServiceGeneric` for open-generic services.
2. Provide one `RegisterServices(Assembly assembly)` extension that reflects over the assembly,
   finds every non-abstract class implementing one of the marker interfaces, and registers it
   against the "real" interface(s) it implements with the lifetime the marker names.
3. Each module ships exactly one small "configurator" entry point — a class implementing a
   shared `IServiceConfiguration`-style contract — whose body is almost always just
   `services.RegisterServices(this.GetType().Assembly)` plus any `services.Configure<TOptions>(section)`
   calls for options binding. The host application only needs to know about these configurator
   entry points (or discover them the same way), never about individual services.
4. When a module is hosted inside a larger framework that already owns DI composition (e.g. a CMS
   with its own service-registration pipeline), the configurator implements that framework's own
   configurator contract instead of the solution's generic one — same shape, different interface,
   so both flavors of module coexist without the host code needing to special-case either.

**When to reach for it:** a solution has (or expects to grow) enough independently-shipped
modules that a hand-maintained central registration list would become a liability. **Not** worth
it for a single-project app or a handful of services — plain `AddFoo()` extensions are simpler and
more discoverable there.

**Reference implementation (SharpPS):** `IServiceConfiguration.Configure(IServiceCollection, IConfiguration)`
(`SharpPS/SharpPS.DependencyInjection/IServiceConfiguration.cs`) is the generic contract; every
feature project's `DependencyInjection/ServiceConfiguration.cs` (or domain-named variant like
`ChatServiceConfigurator`, `SearchConfigurator`) implements it, starting with
`services.RegisterServices(this.GetType().Assembly)` (`SharpServiceCollectionExtensions.cs:20`).
The scanner distinguishes lifetimes via `IService`/`IServiceScoped`/`IServiceSingleton`, routes
`IServiceEnumerable` types through `TryAddEnumerable` (`SharpServiceCollectionExtensions.cs:78-81`),
and unwraps `IServiceGeneric` types to their open generic definition (`SharpServiceCollectionExtensions.cs:37-56`).
Sitecore-hosted modules implement Sitecore's own `IServicesConfigurator.Configure(IServiceCollection)`
(single argument, no `IConfiguration`) instead — same "one configurator per module" shape, different
contract because Sitecore owns that composition root (e.g.
`SharpPS.Sitecore/SharpPS.Sitecore.ChatAI/DependencyInjection/ChatServiceConfigurator.cs`).

## Pattern 2 — Pluggable provider with a fluent registration builder

**Problem:** a capability (storage, messaging transport, auth) needs several interchangeable
backend implementations, selectable by configuration/name, without every call site needing a
`switch` on backend type and without each backend needing bespoke keyed-DI wiring.

**Shape of the pattern:**

1. One interface all backends implement, including a `Name`/`Initialize(string name)` pair — the
   provider is constructed once but can be re-targeted at a named configuration section at
   resolve time (so the same provider type can back two differently-configured named instances).
2. Each concrete provider takes a dual-constructor shape: one constructor accepting a resolved
   options object directly (for tests/manual construction), one accepting `IOptionsMonitor<TOptions>`
   that resolves the *default* named options in the constructor and re-resolves per-name inside
   `Initialize(name)`. This is the actual runtime-selection mechanism — no separate factory
   abstraction needed on top.
3. Registration is a fluent chain: `services.AddCapability(...)` returns a builder; each backend
   ships its own `Use<Backend>(...)` extension on that builder which registers the provider type
   and records which type handles which registered name (e.g. in an options object read later by
   whatever resolves "the provider for name X").
4. New backends require zero changes to the core project — they only add a new `Use<Backend>`
   extension in their own assembly.

**When to reach for it:** a capability genuinely needs multiple swappable backends selected by
name/config, and callers should depend on the shared interface, never a concrete backend type.
**Not** worth it for a capability with exactly one implementation — that's a plain injected
service (Pattern 1's territory), not a provider.

**Reference implementation (SharpPS):** `IStorageProvider<T> where T : StorageItem`
(`SharpPS.Storage/SharpPS.Storage/IStorageProvider.cs`) — `Name`, `Initialize(string name)`,
`ParseOptions`, CRUD, `GetPaged`, `GetUri`. `LocalStorageProvider`
(`SharpPS.Storage/SharpPS.Storage/Providers/LocalStorageProvider.cs:17-32`) shows the dual
constructor and `OPTION_NAME` const. `services.AddStorage(...)` returns a `StorageProviderBuilder`
(`StorageServiceCollectionExtensions.cs:13`); `builder.AddProvider<TProvider>(name)` registers it
transient + enumerable and records the handler type in `StorageFactoryOptions`
(`StorageServiceCollectionExtensions.cs:38-51`). Each backend ships its own `Use<X>Storage`
extension — e.g. `UseGoogleDriveStorage`
(`SharpPS.Storage/SharpPS.Storage.GoogleDrive/GoogleDriveStorageServiceCollectionExtensions.cs`)
calling `builder.AddProvider<GoogleShareDriveStorageProvider>(name)` plus
`AddStream<T>`/`AddChannel(...)` for backend-specific extras. A provider is registered through
this builder, never through Pattern 1's generic marker-interface scan — the builder is what wires
the per-name factory options that plain auto-discovery has no way to express.

## Pattern 3 — Lightweight processor pipeline (`IProcessor<TArgs>` + configurator)

**Problem:** a cross-cutting flow (request handling, a multi-step build/transform) needs an
ordered, independently-extensible sequence of steps, but a full mediator or behavior-pipeline
library is more machinery than the problem needs — steps are added by different modules and must
be reorderable without editing a shared list.

**Shape of the pattern:**

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

**When to reach for it:** the step sequence is genuinely cross-cutting and contributed to by
multiple modules, and needs reordering/insertion without editing existing step code. **Not** worth
it for a fixed, single-module sequence — that's just a method calling other methods in order.

**Reference implementation (SharpPS):** `SharpPS.Pipeline/SharpPS.Pipeline/DependencyInjection/PipelineServiceCollectionExtensions.cs` —
`AddSharpPipeline()` wires `IPipeline<,>`/`IPipelineScope<,>`/`IPipelineManager`;
`AddSharpPipelineConfigurator<TProcessor, TArgs>(patch, scope)` registers one processor plus its
optional collection-patch delegate. Used by ASP.NET Core projects for cross-cutting request
pipelines (e.g. `SharpPS.AspNetCore.Api`'s `ServiceConfiguration`).

This pattern is unrelated to a host framework's own native pipeline/processor engine (e.g.
Sitecore's `CorePipeline`, wired via XML config rather than DI) — a project embedded in such a
host may legitimately use both at once, picking per call site which engine a given step belongs
to. See the sibling `sharpps-sitecore` plugin's `sitecore-pipelines` skill for that pattern set.

## Pattern 4 — Composition-root host bootstrap with plugin-style module loading

**Problem:** hosting several independently-built feature assemblies ("plugins") in one ASP.NET
Core process, where each plugin needs both its DI services (Pattern 1) and its MVC controllers
registered, optionally serving a different feature set per hostname, without the host's
`Program.cs` ever needing to know any plugin's name or reference its assembly at compile time.

**Shape of the pattern:**

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

**When to reach for it:** hosting multiple independently-built/deployed feature modules in one
process (a genuine plugin architecture), especially when different modules should be servable on
different hostnames from a single deployment. **Not** needed for a single-assembly ASP.NET Core
app — that's just the DI/pipeline bootstrap calls directly in a normal `Program.cs`/`Startup`, no
plugin-directory scan or isolated load context involved.

**Reference implementation (SharpPS):** every host `Program.cs` in this solution really is just
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

### What a standard project actually looks like, end to end

`SharpPS.AspNetCore.Administrations` is a real, complete instance of every pattern above wired
together — the shape to copy for a new ASP.NET Core host/module in this solution:

- **`.csproj`**: `Sdk="Microsoft.NET.Sdk.Web"`, multi-targets `net8.0;net9.0;net10.0`, packable
  (`GeneratePackageOnBuild`/`IsPackable`), and pulls in the bootstrap with a single
  `<ProjectReference Include="..\SharpPS.AspNetCore\SharpPS.AspNetCore.csproj" />` — it does
  **not** reference `SharpPS.DependencyInjection`/`SharpPS.Pipeline` directly; those come
  transitively through `SharpPS.AspNetCore`
  (`SharpPS.AspNetCore/SharpPS.AspNetCore.Administrations/SharpPS.AspNetCore.Administrations.csproj`).
  Anything the module itself needs beyond that (here, `Swashbuckle.AspNetCore` for Swagger) is just
  an ordinary extra `<PackageReference>`.
- **`Program.cs`**: exactly `await AspNetHosting.Main(args);` — identical across every host project
  in this solution, confirming Pattern 4's bootstrap call is truly the whole entry point.
- **`api.config.json`** at the project root: the per-module JSON settings file Pattern 4's
  `FeatureBuilderService.Build` auto-layers into `IConfiguration` (it also applies to the host's
  own entry assembly, not only loaded plugins — `AppContext.BaseDirectory` is unioned into the
  scanned paths).
- **`DependencyInjection/ServiceConfiguration.cs`** (the file this skill was written while looking
  at): `IServiceConfiguration.Configure` here does three things in order — (1) Pattern 1's
  `services.RegisterServices(this.GetType().Assembly)` first; (2) ordinary hand-written ASP.NET
  Core wiring specific to this module (`AddAuthorization`, `AddEndpointsApiExplorer`,
  `AddSwaggerGen(...)` reading its own `configuration.GetSection("Api")`) — so `Configure` is not
  *only* the auto-discovery call, it's also where a module does whatever manual service
  registration it needs; (3) Pattern 3 registration for this module's own pipeline steps:
  `services.AddSharpPipelineConfigurator<AdministrationInitialize, InitializeRequestArgs>((x, c) => x.ReplaceWith(x => x.Configurator.ProcessorType == typeof(VariantProcessor), c), Scopes.Default.AspnetCore)`
  followed by `services.AddSharpPipelineConfigurator<VariantProcessor, InitializeRequestArgs>(Scopes.Default.AspnetCore)`
  — a real, working use of the `ReplaceWith` patch operation.
- **`Pipelines/Initialize/AdministrationInitialize.cs`** (`IProcessor<InitializeRequestArgs>`) is
  this module's hook into Pattern 4's startup pipeline (step 5 above): it calls
  `args.Application.UseSwagger()` and maps a Swagger UI under this module's own area path — this is
  *how* a loaded module adds middleware/endpoints during startup without the host needing to know
  about it. **`Pipelines/Initialize/VariantProcessor.cs`** (`IProcessor<RequestArgs>`) shows the
  contravariance point above in practice: it's registered against `InitializeRequestArgs` even
  though it's written against the base `RequestArgs`, and reads `args.RequestServices` to resolve
  an `ILogger<T>` from the ambient scope.

## Two conventions found but *not* worth generalizing

- **A dedicated `Extensions/` folder per project**, holding static extension-method classes named
  `<ExtendedType><Domain>Extensions` (e.g. `SharpPSHttpRequestExtensions.IsBrowserRequest(this HttpRequest ...)`,
  `SharpPS.AspNetCore/SharpPS.AspNetCore/Extensions/SharpPSHttpRequestExtensions.cs`) — a plain C#
  organizational habit, not a mechanism with any auto-discovery or registration behind it.
- **A `docs/` folder per project** exists throughout the solution but every sampled file is an
  empty scaffolding stub (0 lines) — evidence of a project-template artifact, not a documentation
  convention worth replicating. Don't assume `docs/` holds usage information in this solution, and
  don't treat an empty `docs/` folder as a pattern to imitate elsewhere.

## Adjacent convention: EF Core persistence per module

Not a distinct pattern from Pattern 1/2, but a concrete instance worth naming: one
`<Domain>DbContext : SharpDbContext` per storage-backed project, injecting `IDbContextBuilder<T>` +
`DbContextOptions<T>` and overriding `Name`
(`SharpPS.Storage/SharpPS.Storage.EntityFramework/Context/StorageDbContext.cs`), registered with a
fluent chain — `services.AddSharpDbContext<StorageDbContext>(x => ...).AddEntityConfiguration(assembly).AddGenericRepository().AddGenericRepositoryFactory(...)`
(`SharpPS.Storage/SharpPS.Storage.GoogleDrive.Agent/DependencyInjection/ServiceConfiguration.cs`) —
with standard EF Core migrations in a sibling `Migrations/` folder.
