# sharpps-liferay

Liferay knowledge and workflow tooling for solutions built on the [SharpPS](https://github.com/gweone) framework.

## Skills

| Skill | Covers |
|---|---|
| `build` | Running a full Gradle `clean build` from the workspace root and reporting the resulting module `.jar` / client-extension `.zip` output. |
| `deploy` | Copying built module `.jar` / client-extension `.zip` artifacts into the Liferay dev environment's hot-deploy folder. |
| `clean-logs` | Truncating a Docker container's logs to zero without restarting it. |
| `liferay-logs` | Streaming/tailing the `liferay-dev` container's logs via Docker (Compose) and flagging startup, bundle-deploy, and error events. |
| `liferay-batch-client-extension` | Creating/debugging a Liferay "Batch" Client Extension (`type: batch`, `*.batch-engine-data.json`) that imports Object Definitions/Entries/Relationships, List Types, Workflow Definitions, Roles, or User Accounts via the Headless Batch Engine - including the workaround it provides when a Site Initializer can't target a system-required site. |
| `liferay-ddm-field-validation` | Adding/debugging validation rules on a Dynamic Data Mapping (DDM) field shared by Document Types, Objects, and Forms - declarative expression validation vs. a custom `DDMValidation` type. |
| `liferay-document-preview-extension` | Extending/overriding how Document Library renders a file's full-content preview (`<liferay-asset:asset-display>`, DL's "View File" page) via the `DLPreviewRendererProvider` whiteboard SPI - preview vs. thumbnail, stock provider mimetype coverage, the OpenOffice/LibreOffice conversion gate for Office formats, and a worked selectable-text PDF example. |
| `liferay-management-toolbar-search-container` | Wiring `<clay:management-toolbar selectable="true">` with `<liferay-ui:search-container>` + `RowChecker` for bulk-select checkboxes, "select all", and bulk actions in admin JSPs. |
| `liferay-portal-source` | Exploring, navigating, and reasoning about the Liferay Portal source tree - modules, portlets, OSGi components, service builder entities, themes, frontend assets, and Gradle build tasks. |
| `liferay-react-module` | Setting up or adding React to a traditional Liferay OSGi module - deciding module vs. Client Extension first, then scaffolding either a whole React portlet (blade's `npm-react-portlet`) or React mounted from inside a custom JSP/FTL tag. |
| `liferay-site-initializer` | Creating/debugging a Site Initializer that provisions a new Site with pre-built content (pages, web content, documents, objects, blueprints, taxonomies, fragments, roles). |
| `liferay-taglibs` | Choosing and using Liferay JSP taglibs and FreeMarker (FTL) macros, including building a custom taglib from scratch. |
| `liferay-widget-config-erc` | The rule that portlet/widget configuration referencing another Liferay entity must store its ERC, never a raw numeric ID. |

## Action skill workflow: Spec → Plan → Execution

Skills in this plugin that run real commands (not just reference knowledge) follow a standard
three-phase convention — never skip straight to running a command: **Spec** (resolve the
concrete target, asking the user if ambiguous), **Plan** (state the exact command(s) about to
run before running them), **Execution** (run them and report the result). This keeps
deploys/log-clears/builds predictable: what will happen is always spelled out before it happens,
not discovered after the fact in the tool output. See each skill's own `SKILL.md` for how it
applies this to that skill's specific commands.

## Source

These skills originate from a SharpPS Liferay workspace's `.claude/skills` directory, built up
over real project work. This plugin packages the same skills for installation into any
repository via the Claude Code plugin system, independent of that original workspace.
