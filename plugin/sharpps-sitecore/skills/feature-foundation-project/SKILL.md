---
name: feature-foundation-project
description: Add a Feature or Foundation module to an existing SharpPS Sitecore solution using the Sitecore MVC wizard or a sibling project. Look up project naming, src folders, SharpPS.config defaults, scaffolded files, Foundation references, and PackageReference wiring.
---

# Add a Feature or Foundation module

Use for the **Sitecore MVC** project template (`SitecoreProjectWizard`),
not the one-time root website/solution scaffold.
Read the relevant reference sections before creating files.

## Checklist

1. Confirm the layer and module name; ask for missing inputs rather than guessing.
2. Read solution-root `SharpPS.config` when present; its values replace wizard
   prompts. If absent, obtain the setup values from the user.
3. Resolve the project name, location, and every scaffolded target path.
4. For Feature, locate Foundation using `foundationpath` or discovery; report
   a missing Foundation before proceeding instead of silently omitting the reference.
5. Without the wizard, copy and adapt an existing sibling project first.
   Hand-author only when no sibling exists: the reference documents conventions,
   not the actual template file contents.
6. Create the files, wire project/package references, add the project to the
   solution, and report the concrete project name and paths.

## Focused lookup

- [Spec, plan, and execution](references/project-scaffolding.md#workflow-spec---plan---execution)
- [Copying a sibling without the VS wizard](references/project-scaffolding.md#without-the-vs-wizard-copy-a-sibling-project-dont-hand-author-from-scratch)
- [Project naming and src locations](references/project-scaffolding.md#naming-and-location-convention)
- [Scaffolded files, publish actions, and the Include/Feature quirk](references/project-scaffolding.md#what-gets-scaffolded)
- [SharpPS.config keys and wizard tokens](references/project-scaffolding.md#sharppsconfig-supplies-the-rest---no-prompting-if-its-already-there)
- [Foundation discovery and Feature package behavior](references/project-scaffolding.md#feature-projects-auto-reference-the-foundation-project)
- [Classic csproj and PackageReference format](references/project-scaffolding.md#project-file-format)

## Constraints to retain

- Foundation scaffolding still uses `Include/Feature/`: preserve that wizard
  behavior when replicating its files, rather than silently correcting it.
- Feature gets the Foundation `ProjectReference` and no wizard package list;
  Foundation gets the full package list. Edit packages in `.csproj`, not `packages.config`.
- Area `Views/Web.config` publishes; root web configs do not. The host site owns
  runtime `Web.config`.

## Related skills

- [sitecore-solution-config](../sitecore-solution-config/SKILL.md) — solution-root configuration.
- [sitecore-pipelines](../sitecore-pipelines/SKILL.md) — add processors and pipeline config to a module.
