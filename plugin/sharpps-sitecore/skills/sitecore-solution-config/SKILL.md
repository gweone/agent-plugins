---
name: sitecore-solution-config
description: Look up SharpPS.config in a Sitecore solution. Use for instance URL, publish path, core/area naming, credential precedence, wizard defaults, or Start-Pipeline automatic argument resolution.
---

# SharpPS Sitecore solution configuration

Read the solution's values before constructing paths or connecting.
This skill does not authorize instance access or deployment.

## Workflow

1. Locate `SharpPS.config` at the **solution root**, not in a physical
   `.configuration/` directory. Inspect only the values needed for the task.
2. Use `url` for the instance, `publishpath` for the IIS webroot, and
   `core`/`area` for solution path conventions. Tenant/Site is separate:
   ask the user; do not infer it from this file.
3. Resolve each SPE credential independently: explicit user override →
   populated config element → cmdlet default (`sitecore\admin` / `b`).
   The file is optional for SPE; do not create it or ask for credentials
   merely because it is absent. Do not try defaults before configured values.
4. Preserve configured password whitespace, never print or persist secrets,
   and pass resolved credentials explicitly to `New-SPESession`.
   On authentication failure, stop and ask for corrected credentials.
5. For pipelines, distinguish the resolver's current directory from a
   supplied solution path. `Sitecore`, `Publish`, and `Artifact` resolve
   arguments from the solution-root working directory; not all pipelines do.

## Lookup

| Need | Reference |
|---|---|
| XML schema, file location, wizard fallback | [Solution values](references/configuration.md#where-a-solutions-basic-sitecore-info-lives) |
| Optional username/password, partial config, precedence example | [Credential resolution](references/configuration.md#spe-credentials-resolve-from-sharppsconfig-before-connecting) |
| 00-Resolve-SharpPS, -Args overrides, pipeline-specific defaults | [Pipeline resolution](references/configuration.md#pipelines-resolve-it-by-default---no-need-to-pass--args) |

## Related skills

- [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md): HTTP/SPE connection differences.
- [feature-foundation-project](../feature-foundation-project/SKILL.md): wizard/scaffold usage.
- [sitecore-template-items](../sitecore-template-items/SKILL.md): item path conventions.
