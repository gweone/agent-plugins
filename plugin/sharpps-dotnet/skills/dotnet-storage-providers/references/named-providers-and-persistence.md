# Pattern 2 — Pluggable provider with a fluent registration builder

## Evidence and packages

The original source trace below describes the historical external SharpPS solution, not plugin
files or newly tested APIs. Consume `SharpPS.Storage` and the needed backend packages, rather
than copying the provider builder/factory core. See
[package roles and evidence scope](../../dotnet-service-registration/references/packages-and-evidence.md).

## Problem and fit

A capability (storage, messaging transport, auth) needs several interchangeable
backend implementations, selectable by configuration/name, without every call site needing a
`switch` on backend type and without each backend needing bespoke keyed-DI wiring.

Use when a capability genuinely needs multiple swappable backends selected by name/config, and
callers should depend on the shared interface, never a concrete backend type. For exactly one
implementation, use a plain injected service
([Pattern 1](../../dotnet-service-registration/SKILL.md)), not a provider.

## Named options and fluent registration

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

`AddCapability`/`Use<Backend>` describe the shape, not literal SharpPS API names. The concrete
storage entry points and transient lifetime are traced below; named initialization does not
imply a singleton provider shared across requests.

## Storage source trace

`IStorageProvider<T> where T : StorageItem`
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

## Adjacent convention: EF Core persistence per module

Not a distinct pattern from Pattern 1/2, but a concrete instance worth naming: one
`<Domain>DbContext : SharpDbContext` per storage-backed project, injecting `IDbContextBuilder<T>` +
`DbContextOptions<T>` and overriding `Name`
(`SharpPS.Storage/SharpPS.Storage.EntityFramework/Context/StorageDbContext.cs`), registered with a
fluent chain — `services.AddSharpDbContext<StorageDbContext>(x => ...).AddEntityConfiguration(assembly).AddGenericRepository().AddGenericRepositoryFactory(...)`
(`SharpPS.Storage/SharpPS.Storage.GoogleDrive.Agent/DependencyInjection/ServiceConfiguration.cs`) —
with standard EF Core migrations in a sibling `Migrations/` folder.

This is limited evidence for that consuming solution's persistence registration, not a general
EF Core migration, schema design, or database deployment guide.
