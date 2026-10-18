# Pattern 1 — Convention-based service auto-registration

## Evidence and package boundary

This is the original marker-interface pattern and source trace, not a new scanner implementation.
Consume `SharpPS.DependencyInjection`; the mechanism below explains its behavior, not code to
copy into each module. Paths and line numbers refer to the historical external SharpPS solution,
not this plugin; API behavior has not been newly tested. See
[package roles and evidence scope](packages-and-evidence.md).

## Problem and fit

A solution with dozens of independently-shipped projects doesn't want one central
`Startup`/`Program` that hand-lists every service (`services.AddScoped<IFoo, Foo>(); ...`) from
every project — that file becomes a bottleneck and a merge-conflict magnet, and it's easy to ship
a new project without wiring it in at all.

Use this when enough independently-shipped modules make a hand-maintained central registration
list a liability. For a single-project app or a handful of services, plain `AddFoo()` extensions
are simpler and more discoverable.

## Marker lifetimes and module entry point

1. The package defines empty marker interfaces distinguishing lifetime/registration shape —
   `IService` (transient), `IServiceScoped`, `IServiceSingleton`, plus `IServiceEnumerable`
   for types that should be added with `TryAddEnumerable` (multiple implementations of the same
   interface expected to coexist) and `IServiceGeneric` for open-generic services.
2. Its `RegisterServices(Assembly assembly)` extension reflects over the assembly,
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

## Source trace and Sitecore boundary

`IServiceConfiguration.Configure(IServiceCollection, IConfiguration)`
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

Register Sitecore's configurator in XML under `<services><configurator>` with a
`type="Namespace.Configurator, Assembly"` attribute; generic host discovery does not replace that hook.
The generic host's assembly/configurator discovery is owned by
[dotnet-module-hosting](../../dotnet-module-hosting/SKILL.md).
Named storage providers instead use their
[fluent builder](../../dotnet-storage-providers/SKILL.md), not this marker scan.
