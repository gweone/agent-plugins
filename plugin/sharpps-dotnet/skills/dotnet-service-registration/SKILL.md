---
name: dotnet-service-registration
description: Register SharpPS .NET module services with marker-interface assembly scanning. Use for IService, IServiceScoped, IServiceSingleton, IServiceEnumerable, IServiceGeneric, RegisterServices, and IServiceConfiguration; distinguish generic DI configuration from Sitecore IServicesConfigurator.
---

# .NET module service registration

Use for Pattern 1: package-backed convention registration in independently
shipped .NET modules. For a handful of services, plain `AddFoo()` is simpler.

## Checklist

1. Consume `SharpPS.DependencyInjection`; do not copy its scanner internals.
2. Choose the intended lifetime marker: `IService` is transient,
   `IServiceScoped` is scoped, and `IServiceSingleton` is singleton.
3. Use `IServiceEnumerable` for coexistence via `TryAddEnumerable` and
   `IServiceGeneric` for open-generic registration; check the resolved version.
4. Provide a module `IServiceConfiguration.Configure(IServiceCollection,
   IConfiguration)` entry point; start with
   `services.RegisterServices(this.GetType().Assembly)`.
5. Bind module options with `services.Configure<TOptions>(section)` and add
   ordinary manual registrations there when needed.
6. Let the host invoke module configurators. In a SharpPS modular host,
   features do not repeat `AddSharpPSAspnetCore()`/`AddSharpPipeline()`.

## Focused lookup

- [Marker lifetimes and per-module configurator shape](references/marker-registration.md#marker-lifetimes-and-module-entry-point).
- [Scanner source trace and Sitecore contract difference](references/marker-registration.md#source-trace-and-sitecore-boundary).
- [Package roles and historical evidence scope](references/packages-and-evidence.md).

## Boundaries

- Sitecore owns its composition root: use its
  `IServicesConfigurator.Configure(IServiceCollection)` contract and registration,
  not generic host configurator discovery as a substitute.
- Named storage providers require their fluent builder and per-name factory
  options; marker scanning alone cannot express that registration.
- Source paths in references are historical consuming-repo evidence, not plugin
  files or newly tested package APIs.

## Related skills

- [dotnet-storage-providers](../dotnet-storage-providers/SKILL.md) — named provider builder.
- [dotnet-module-hosting](../dotnet-module-hosting/SKILL.md) — host assembly/configurator discovery.
- [dotnet-processor-pipelines](../dotnet-processor-pipelines/SKILL.md) — C# step contributions.
