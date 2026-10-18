---
name: dotnet-storage-providers
description: Configure or extend SharpPS named storage providers with IStorageProvider, AddStorage, StorageProviderBuilder, UseGoogleDriveStorage and other backend extensions, named options, and Initialize(name). Includes the limited SharpDbContext per-module persistence example; not marker-interface provider registration.
---

# .NET named storage providers

Use for Pattern 2: multiple interchangeable storage backends selected by name
or configuration. A single implementation usually needs only ordinary DI.

## Checklist

1. Consume `SharpPS.Storage` and only the backend packages needed by the host;
   do not copy builder/factory internals into feature projects.
2. Implement the shared `IStorageProvider<T> where T : StorageItem` contract,
   including `Name` and `Initialize(string name)`, for a new backend.
3. Preserve the dual-constructor shape: direct options for manual/test use,
   `IOptionsMonitor<TOptions>` for default and per-name runtime options.
4. Register with `services.AddStorage(...)` and backend `Use<X>Storage`
   extensions. A new backend extension calls `builder.AddProvider<TProvider>(name)`.
5. Keep named initialization aligned with registered options. The builder
   registers transient + enumerable providers and records per-name handler types.
6. Add backend-specific stream/channel services through its extension as needed;
   no changes to the core project are needed for a new backend.

## Focused lookup

- [Named options, dual constructors, and fluent registration](references/named-providers-and-persistence.md#named-options-and-fluent-registration).
- [Storage interface, LocalStorageProvider, Google Drive, and factory source trace](references/named-providers-and-persistence.md#storage-source-trace).
- [SharpDbContext and the per-module EF Core registration chain](references/named-providers-and-persistence.md#adjacent-convention-ef-core-persistence-per-module).
- [Packages and historical source/version scope](../dotnet-service-registration/references/packages-and-evidence.md).

## Boundaries

- Use the provider builder, not generic marker-interface scanning: the builder
  wires per-name factory options that ordinary auto-discovery cannot express.
- Named reinitialization is not a reason to share one singleton provider across
  requests; preserve the traced transient registration.
- The EF Core note preserves one consuming-solution example, not a general
  migration, schema-design, or database deployment guide.
- Source traces are historical external examples, not files in this plugin or
  newly tested package APIs. Verify the consuming project's resolved version.

## Related skills

- [dotnet-service-registration](../dotnet-service-registration/SKILL.md) — ordinary service lifetimes/configurators.
- [dotnet-module-hosting](../dotnet-module-hosting/SKILL.md) — host and feature configuration ownership.
