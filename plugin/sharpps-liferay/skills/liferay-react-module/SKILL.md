---
name: liferay-react-module
description: >
  Choose and wire React/TypeScript in a traditional Liferay OSGi module: npm-react-portlet/esbuild versus tag-mounted liferay-npm-scripts, shared React externals/imports, npmscripts.config.js and Gradle copyNpmBuild. Decide Client Extension versus portlet/tag before scaffolding.
---

# Liferay React module

Use for npm/toolchain/container wiring, not the Java mounting API or custom
JSP/FTL tag registration. References preserve generated-template and existing-module
evidence from another consuming workspace; resolve its equivalent here first.

## Workflow

1. Follow **Spec → Plan → Execution**. Read `liferay.workspace.product` and/or
   `target.platform.version` from the consuming workspace's `gradle.properties`.
2. Before choosing a traditional module, inspect local rules. Below 7.4 it is
   the normal default; on 7.4/Quarterly Releases consider a Custom Element CX
   for a standalone page widget without JSP/FTL or portlet lifecycle needs.
3. Ask what React renders inside. JSP/FTL tag integration or a genuine MVC
   portlet lifecycle justifies OSGi; do not guess the container.
4. Pick **A: whole React portlet** (blade npm-react-portlet, esbuild, external
   React, view.jsp import) or **B: tag-mounted React** (npm-scripts, TypeScript,
   shared React imports and a barrel export). Keep the mechanisms distinct.
5. State the exact proposed scaffold/files, module/package and authorized
   verification steps before mutation. Historical commands are in references,
   not permission to scaffold, build or deploy now.
6. For pattern B, wire npm output into the JAR with the Node plugin and
   `copyNpmBuild`; verify the generated pattern A actually wires its output too.
7. Route Java mounting to [liferay-react-taglib](../liferay-react-taglib/SKILL.md)
   and TLD/capability registration to [liferay-custom-taglib](../liferay-custom-taglib/SKILL.md).

## Critical constraints

- Preserve esbuild `--external:react --external:react-dom` in A, and imports
  from `@liferay/frontend-js-react-web` in B. A second React copy causes invalid
  hooks/context errors; use the target portal's shared runtime.
- Pattern A's default `function(elementId)` and JSP positional call must agree.
  Pattern B's `{ExportName} from package-name` must resolve through its barrel.
- Blade's source-inspected/generated example auto-detected product/version
  inside a real workspace; explicit version flags were a fallback for missing context.
- `tsconfig.json.disabled` did not block the observed npm-scripts transpilation;
  enabling editor type-checking is a separate choice, not a required build fix.
- A TLD `Provide-Capability` is needed for JSP/FTL invocation, not merely because
  code calls ReactRenderer. Do not duplicate Java mounting internals here.

## Focused references

- [Container decision, generated files and complete portlet examples](references/module-choice-and-portlet.md)
- [Tag-mounted package/config/Gradle examples and tsconfig quirk](references/tag-module-toolchain.md)
- [Original workflow, build/deployment examples and verification evidence](references/workflow-and-verification.md)

`modules/search` is an external reference application, not a plugin-local path.
