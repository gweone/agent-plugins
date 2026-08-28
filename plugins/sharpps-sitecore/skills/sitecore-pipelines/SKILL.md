---
name: sitecore-pipelines
description: General patterns for authoring and wiring C# processors into Sitecore's native XML-configured pipeline engine (Sitecore.Pipelines.CorePipeline) — extending a built-in pipeline (initialize, owin.initialize, httpRequestProcessed, mvc.*) with patch:before/patch:after processors, versus defining a brand-new custom pipeline invoked with CorePipeline.Run(name, args[, domain]). Covers a convenience-args base pattern, chaining pipeline stages, a scoped-logging leading-processor pattern, the standard App_Config/Include/{Feature|Foundation}/{SolutionName}/ config path, and config-binding conventions. Each pattern has a verified reference implementation from SharpPS.Sitecore. For a general (non-Sitecore) C# processor-pipeline pattern, see sharpps-dotnet's dotnet-service-patterns skill instead. Use when adding or designing a Sitecore pipeline processor.
---

# Patterns for Sitecore's native pipeline engine

Any Sitecore solution can extend Sitecore's own XML-configured pipeline engine
(`Sitecore.Pipelines.CorePipeline`) in two distinct ways — extend something Sitecore already runs,
or define an entirely new named pipeline of your own — plus a handful of supporting conventions
that make custom pipelines easier to work with. Each pattern below is illustrated with a verified
reference implementation from the SharpPS.Sitecore solution, but none of it depends on SharpPS
specifically — it applies to any Sitecore MVC solution authoring custom pipeline processors.

## Pattern 1 — extending a built-in Sitecore pipeline

Subclass the matching Sitecore base processor and patch it into an existing pipeline by XML. No DI
registration is involved — the config patch *is* the registration.

**Reference implementation:**
- `RequestLogger : HttpRequestProcessor` — `Process(HttpRequestArgs args)`
  (`SharpPS.Sitecore/SharpPS.Sitecore/Pipelines/Request/RequestLogger.cs`).
- `HttpStatusHandler : HttpRequestProcessor` for `httpRequestProcessed`
  (`SharpPS.Sitecore/SharpPS.Sitecore/Pipelines/HttpRequestProcessed/HttpStatusHandler.cs`).
- `InitializeSwaggerUI` patched into `owin.initialize` with `patch:before="*"` positioning:

```xml
<!-- SharpPS.Sitecore.SwaggerUI/App_Config/Modules/SharpPS/SharpPS.SwaggerUI.config -->
<owin.initialize>
  <processor type="SharpPS.Sitecore.SwaggerUI.Pipelines.Initialize.InitializeSwaggerUI, SharpPS.Sitecore.SwaggerUI" patch:before="*">
    <DefaultApiRoute>true</DefaultApiRoute>
    <Namespaces hint="list">
      <namespace>Sitecore.Services.Infrastructure.*</namespace>
    </Namespaces>
  </processor>
</owin.initialize>
```

**Config-binding rule (applies to both patterns below too):** every public settable property on a
processor is readable as a same-named XML child element — Sitecore's reflection-based binder sets
it before `Process` runs. A collection property needs `hint="list"` (repeat the element per item,
as above); a dictionary/multi-map property needs `hint="raw:AddPropertyMap"` with a custom `Add*`
method, as in a JSON item builder processor's
`<itemPropertyMaps hint="raw:AddPropertyMap"><map property="..." resolveName="..."/></itemPropertyMaps>`
(`SharpPS.Sitecore.JsonHandler/App_Config/Include/Examples/JsonItemHandler.config.example`).

## Pattern 2 — defining a brand-new custom pipeline

For a self-contained feature (search, a JSON item handler, SAML), define your own named
pipeline(s) from scratch and call them explicitly — Sitecore's engine doesn't care whether a
pipeline name is "built-in"; any name registered under `<sitecore><pipelines>` works the same way.

Two registration styles, chosen by whether the pipeline needs per-feature-instance domain scoping:

**Flat, dotted name** — one global pipeline, invoked with no domain argument. Reference
implementation:

```xml
<!-- SharpPS.Sitecore.ContentSearch/App_Config/Modules/SP Content Search/SharpPS.Sitecore.ContentSearch.config -->
<spsearch.getdefinition>
  <processor type="SharpPS.Sitecore.ContentSearch.Pipelines.GetDefinition.GetFromDataSource, SharpPS.Sitecore.ContentSearch"/>
  <processor type="SharpPS.Sitecore.ContentSearch.Pipelines.GetDefinition.GetFromRendering, SharpPS.Sitecore.ContentSearch"/>
</spsearch.getdefinition>
```
```csharp
CorePipeline.Run("spsearch.getdefinition", args);  // SharpPS.Sitecore.ContentSearch/ContentSearchRenderer.cs:80
```

**Domain-scoped group** — `<group groupName="X">` wraps several named sub-pipelines that must be
resolvable per feature instance/site, invoked with a third `domain` argument matching `groupName`.
Reference implementation:

```xml
<!-- SharpPS.Sitecore.JsonHandler .config.example -->
<group groupName="jsonItemHandler" name="jsonItemHandler">
  <pipelines>
    <request>...</request>
    <builder>...</builder>
    <fieldbuilder>...</fieldbuilder>
    <render>...</render>
  </pipelines>
</group>
```
```csharp
CorePipeline.Run("request", requestArgs, args.PipelineDomain); // JsonItemRequestHandler.cs:26
```

The SAML2 module in this solution uses the same group mechanism
(`<group groupName="Saml2"><pipelines><command>...</command><session>...</session></pipelines></group>`,
`SharpPS.Sitecore.Saml2/App_Config/Include/Examples/SharpPS.Sitecore.Saml2.config.example`).

**Rule:** use the flat dotted-name style when one pipeline definition serves the whole instance; use a
`<group groupName="X">` when the same sub-pipeline *names* (`request`, `builder`, `render`, ...) must
stay isolated per feature/module — the group name is what disambiguates them at `CorePipeline.Run` time.

**Chaining rule:** a later stage is triggered by calling `CorePipeline.Run` again *from inside* an
earlier processor, not by any built-in "next pipeline" mechanism — e.g. a JSON item builder
processor calls `CorePipeline.Run("fieldbuilder", builderArgs, args.PipelineDomain)`
(`JsonItemBuilderProcessor.cs:101`), and the request handler itself chains `request` → `builder` →
`render`.

## Pattern 3 — an ambient-context args base for DI/logging inside processors

Sitecore's `CorePipeline.Run` only requires a class with a `Process(TArgs)` method reachable by
reflection — no interface or common base is mandatory. Proof: a trace-log processor
(`SharpPS.Sitecore/SharpPS.Sitecore/Pipelines/Log/TraceLogProcessor.cs`) declares
`Process(PipelineArgs args)` with no base class and no `override`, and still runs correctly as a
pipeline step. That means a custom pipeline's args class is free real estate: nothing stops it
from carrying more than raw pipeline state.

**The pattern:** give custom-pipeline args classes a shared base that resolves an ambient DI scope
and a named logger lazily, instead of threading a `IServiceProvider`/`ILogger` parameter through
every processor call — each processor just reads `args.ServiceProvider`/`args.Logger`.

**Reference implementation:** `SharpPipelineArgs : PipelineArgs, IDisposable` and
`SharpMvcPipelineArgs : MvcPipelineArgs` (`SharpPS.Sitecore/SharpPS.Sitecore/Pipelines/`) add
`ServiceProvider` (falls back to `Sitecore.DependencyInjection.ServiceLocator.ServiceProvider` when
not explicitly set), `Logger` (resolved by name on first access), and a `PipelineDomain` string
threaded through a parent-args copy constructor. `SharpPipelineProcessor<TArg> where TArg : SharpPipelineArgs`
adds a typed `public abstract void Process(TArg args)` convenience base, used by every command
processor in the SAML2 module (`AcsCommand : SharpPipelineProcessor<Saml2Args>`,
`SharpPS.Sitecore.Saml2/Pipelines/Command/AcsCommand.cs`). Most custom-pipeline args classes in
this solution derive from the base (ContentSearch's `GetDefinitionArgs`/`GetQueryArgs`/
`GetRenderingArgs`/`SearchArgs`, JsonHandler's `Json*Args`, SAML2's `Saml2Args`/`SessionArgs`); a
trivial cross-cutting processor with no DI/logging need can stay on plain `PipelineArgs` with no
base at all.

## Pattern 4 — a scoped-logging leading processor

**The pattern:** rather than each processor picking its own log scope, put one small processor
first in the pipeline whose only job is to stash a scope name into shared pipeline state (e.g.
`CustomData`) that every later processor's logging call reads back — the scope becomes a
declarative, config-set value instead of something hardcoded per processor.

**Reference implementation:** `TraceLogProcessor`
(`SharpPS.Sitecore/SharpPS.Sitecore/Pipelines/Log/TraceLogProcessor.cs`) sets
`args.CustomData["Logger"]` from its `Scope` property so every later processor's logger-resolution
call picks up that name, and optionally dumps a stack trace when `Track=true`:

```xml
<command>
  <processor type="SharpPS.Sitecore.Pipelines.Log.TraceLogProcessor, SharpPS.Sitecore">
    <Scope>Logger</Scope>
  </processor>
  ...
</command>
```

## Adjacent convention: Sitecore's own DI hook (`<services><configurator>`)

Sitecore-hosted code registers services via Sitecore's own
`IServicesConfigurator.Configure(IServiceCollection services)` (single argument, no
`IConfiguration`), declared in config rather than auto-discovered:

```xml
<services>
  <configurator type="SharpPS.Sitecore.ContentSearch.DependencyInjection.SearchConfigurator, SharpPS.Sitecore.ContentSearch" />
</services>
```

This is a different mechanism from a generic marker-interface/assembly-scan DI-registration
pattern used outside a Sitecore host (see the sibling `sharpps-dotnet` plugin's
`dotnet-service-patterns` skill, Pattern 1) — don't mix them: code that only runs inside Sitecore
registers through `<services><configurator>`.

## Adjacent convention: where the config file lives

**Standard location for a new module's pipeline config:** `App_Config/Include/{Feature|Foundation}/{SolutionName}/<ModuleName>.config`
— the layer folder (`Feature` or `Foundation`) matching the module's own layer, then a folder
named for the solution, then the config file itself. This is the same Helix-style path the
"Sitecore MVC" project wizard scaffolds for a brand-new Feature/Foundation project's own settings
config (see the `feature-foundation-project` skill's "What gets scaffolded" table) — reuse it for
a new pipeline's config rather than inventing another location. **Known quirk to account for:**
that wizard template hardcodes the `Feature` segment unconditionally, so a wizard-generated
Foundation project's scaffolded configs land under `Include/Feature/{SolutionName}/`, not
`Include/Foundation/{SolutionName}/` — don't silently "fix" that when replicating a
wizard-generated file by hand, but do use the correct `Foundation` segment when hand-authoring a
new config for a Foundation-layer module from scratch, since the quirk is specific to that one
template, not a solution-wide rule.

Independently of *where* the file lives, decide *whether* it ships live or inert: some pipelines
in this solution (SAML2, JsonHandler) ship only an `App_Config/Include/Examples/*.config.example`
— inert until copied out of `Examples/` and renamed to `.config`, because it needs
environment-specific values filled in (certificate paths/passwords, root item paths, route names).
Others (ContentSearch, SwaggerUI) ship a live, already-active config directly under
`App_Config/Modules/<Name>/*.config` — an older, pre-Helix location still present from before this
convention, not one to copy for new modules. When adding a new custom pipeline that needs secrets
or per-site values before it's safe to enable, ship it as `{ModuleName}.config.example` under the
module's own `Include/{Feature|Foundation}/{SolutionName}/` folder; when it's safe with sane
defaults, ship a live `.config` there instead.
