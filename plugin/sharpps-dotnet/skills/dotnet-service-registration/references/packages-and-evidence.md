# Package roles and evidence boundaries

## Evidence scope

These notes preserve the source traces from the original four-pattern skill: a historical
SharpPS consuming solution spanning .NET Framework and .NET Core/Standard. Backticked
`SharpPS/...`, `SharpPS.Storage/...`, `SharpPS.Pipeline/...`, `SharpPS.AspNetCore/...`, and
`SharpPS.Sitecore/...` paths identify that external solution, not files in this plugin.
Line numbers and target frameworks describe the inspected snapshot, not guarantees for
all package versions. The split into focused skills did not re-test these APIs or inspect
new package binaries. Check the consuming project's resolved versions/source before use.

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
references `SharpPS.AspNetCore` and calls its bootstrap ([Pattern 4](../../dotnet-module-hosting/SKILL.md)); an ordinary **feature
module** hosted inside it only needs `SharpPS.DependencyInjection`/`SharpPS.Pipeline` directly (or
transitively) and never calls `AddSharpPSAspnetCore()`/`AddSharpPipeline()` itself — the host's
bootstrap wires those once for every module it loads.

## Two conventions found but not worth generalizing

- **A dedicated `Extensions/` folder per project**, holding static extension-method classes named
  `<ExtendedType><Domain>Extensions` (e.g. `SharpPSHttpRequestExtensions.IsBrowserRequest(this HttpRequest ...)`,
  `SharpPS.AspNetCore/SharpPS.AspNetCore/Extensions/SharpPSHttpRequestExtensions.cs`) — a plain C#
  organizational habit, not a mechanism with any auto-discovery or registration behind it.
- **A `docs/` folder per project** exists throughout the solution but every sampled file is an
  empty scaffolding stub (0 lines) — evidence of a project-template artifact, not a documentation
  convention worth replicating. Don't assume `docs/` holds usage information in this solution, and
  don't treat an empty `docs/` folder as a pattern to imitate elsewhere.

## Focused owners

- [Pattern 1: service registration](../../dotnet-service-registration/SKILL.md).
- [Pattern 2: named storage providers](../../dotnet-storage-providers/SKILL.md).
- [Pattern 3: C# processor pipelines](../../dotnet-processor-pipelines/SKILL.md).
- [Pattern 4: module hosting](../../dotnet-module-hosting/SKILL.md).
