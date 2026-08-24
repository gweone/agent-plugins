# sharpps-sitecore

Sitecore/SXA knowledge for solutions built on the [SharpPS](https://github.com/gweone) framework.

## Skills

| Skill | Covers |
|---|---|
| `sitecore` | Interacting with a running Sitecore instance via the `SharpPS.Shells` PowerShell module - bootstrapping, `SharpPS.config`, pipeline auto-resolution, logging in (`New-SitecoreSession`), reading the live merged config, and creating/manipulating CMS items (templates, renderings, datasources) via SPE (`New-SPESession`). |
| `sxa-search` | Sitecore XA's native search feature - `Sitecore.XA.Feature.Search.Controllers.SearchController` and the `/sxa/search/*` Web API endpoints: routes, query string params (including `sc_site`/`sc_database`/facet filtering), response shapes, and how Rendering Variants (`v`/`VariantID`) render each result's `Html`. |
| `feature-foundation-project` | Adding a new Feature or Foundation layer project to an existing SharpPS Sitecore solution via the "Sitecore MVC" VS project template - naming/location convention, what gets scaffolded, and Feature's automatic `ProjectReference` to the Foundation project. |
| `sxa-cshtml-controller-rendering` | Wiring a `.cshtml` up as a Controller Rendering with a custom view path (instead of a View Rendering) - reusing the existing `Sitecore.XA.Foundation.Mvc.Controllers.StandardController` with no new controller code, and converting an existing rendering item's template via SPE. |
| `sitecore-pipelines` | General patterns for authoring and wiring C# processors into Sitecore's own native `CorePipeline` engine, each with a verified SharpPS.Sitecore reference implementation: extending a built-in Sitecore pipeline (`initialize`, `owin.initialize`, `httpRequestProcessed`, `mvc.*`) via an App_Config patch vs. defining a brand-new custom pipeline (flat dotted name like `myfeature.getdefinition`, or a domain-scoped `<group groupName="X">`) invoked with `CorePipeline.Run(name, args[, domain])`; an ambient-context args-base pattern for DI/logging inside processors; a scoped-logging leading-processor pattern; `<services><configurator>` DI registration; the standard `App_Config/Include/{Feature\|Foundation}/{SolutionName}/` config path plus `.config.example` vs. live module config files; and config-binding rules (`hint="list"`/`hint="raw:AddPropertyMap"`). Distinct from a general (non-Sitecore) C# pipeline pattern for plain code — see the `sharpps-dotnet` plugin's `dotnet-service-patterns` skill for that one. |
| `html-to-datasource` | Solution-agnostic guidance for converting a rendering's hardcoded HTML/`.cshtml` (wording, validation parameters/messages, option lists, links) into a real Sitecore-driven datasource: classifying every literal into a field, grouping fields into Template Sections instead of a flat list, the Shared-field rule for non-translatable parameters (no per-language instance), a repeatable-option-list child-item pattern, per-language `__Standard Values` defaults for every supported language, detecting View vs. Controller Rendering from how the component is actually invoked and wiring its `Datasource Template`/`Datasource Location` fields, and the mandatory approval gate (template path, datasource path, rendering type, field design, and Standard Values) before anything is created in Sitecore. Builds on the `sitecore` skill's template/rendering/datasource creation mechanics rather than duplicating them. |

## Source

These skills originate from `SharpPS.VisualStudio`'s `solutionitems.vstemplate`,
which scaffolds them into every new SharpPS Sitecore solution under
`.claude/skills/`. This plugin packages the same skills for installation into
any repository via the Claude Code plugin system, independent of that
template.
