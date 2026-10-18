---
name: sitecore-pipelines
description: Add a C# processor to initialize, owin.initialize, httpRequestProcessed, or mvc.*; define a custom Sitecore CorePipeline.Run pipeline. Look up patch ordering, XML property binding, domain groups, pipeline args, logging scope, services configurators, and config placement.
---

# Sitecore pipeline processors

Use for Sitecore's native XML-configured `Sitecore.Pipelines.CorePipeline`,
not a general-purpose C# processor pipeline. The reference retains verified
SharpPS.Sitecore examples; the patterns apply to Sitecore MVC solutions generally.

## Checklist

1. Decide whether to extend an existing pipeline or define a new named pipeline.
2. For a built-in pipeline, use its matching processor base and XML patch
   placement (`patch:before`/`patch:after`); the patch is the registration.
3. For a custom pipeline, choose a global dotted name or a domain-scoped
   `<group groupName="X">`; pass the matching domain to `CorePipeline.Run`.
4. Define `Process(TArgs)` and any shared args/DI/logging state needed.
   Chain stages explicitly with another `CorePipeline.Run` call.
5. Bind configurable properties in XML; use the documented list/raw-map hints.
6. Put new config in the module's layer/solution Include folder. Decide whether
   it is safe to enable immediately or must remain an inert `.config.example`.

## Focused lookup

- [Built-in pipelines, patch positioning, and XML property binding](references/pipeline-patterns.md#built-in-pipelines)
- [Custom dotted names, domain groups, and chaining](references/pipeline-patterns.md#custom-pipelines)
- [Shared args, ambient service provider, logger, and typed processor base](references/pipeline-patterns.md#pipeline-args)
- [Leading processor for config-defined logging scope](references/pipeline-patterns.md#scoped-logging)
- [Sitecore IServicesConfigurator registration](references/pipeline-patterns.md#services-configurator)
- [Config location, wizard quirk, live versus example files](references/pipeline-patterns.md#config-location)

## Constraints to retain

- Register Sitecore-hosted services through `<services><configurator>`, not
  the generic marker-interface/assembly-scan mechanism.
- New config: `App_Config/Include/{Feature|Foundation}/{SolutionName}/`.
  Do not copy legacy `App_Config/Modules/` locations into new modules.
- Replicating wizard-generated Foundation files preserves their hardcoded
  `Include/Feature/` quirk; a newly hand-authored Foundation config uses `Foundation`.
- Config requiring secrets or per-site values stays `.config.example` until
  configured and explicitly enabled; do not ship it active by default.

## Related skills

- [feature-foundation-project](../feature-foundation-project/SKILL.md) — module scaffolding and its config-path quirk.
- [sitecore-solution-config](../sitecore-solution-config/SKILL.md) — solution-root configuration.
