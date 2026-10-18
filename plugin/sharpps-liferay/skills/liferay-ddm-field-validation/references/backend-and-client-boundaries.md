# Backend enforcement versus browser UX

[Skill workflow and reference index](../SKILL.md)

> Evidence scope: retained from source tracing and live debugging in an earlier consuming
> Liferay workspace, not executed or re-verified in this plugin repository. Resolve the
> current workspace, target release and applicable local rules before applying examples.
> `modules/search` (`sharpps-search`), `client-extensions/liferay-global-extension`,
> initializer paths, `.claude/rules/cx.md`/`CLAUDE.md`, `configs/local`, `bundles`, and
> container `liferay-dev` are external workspace examples, not plugin-local files or links.
> Resolve `$LIFERAY_PORTAL` with [liferay-portal-source](../../liferay-portal-source/SKILL.md)
> for source citations; line numbers describe the inspected snapshot, not every release.
> Headings retain original numbering for provenance; navigation uses topical links.

## 4. Not achievable via Client Extension — confirmed, not assumed

Checked every registered `@CETType` in
`client-extension-type-api` (`$LIFERAY_PORTAL/modules/apps/client-extension/client-extension-type-api/src/main/java/com/liferay/client/extension/type/`):
`fdsCellRenderer`, `fdsFilter`, `customElement`, `iframe`, `themeCSS`, `globalJS`, `globalCSS`,
`staticContent`, `themeFavicon`, `jsImportMapsEntry`, `themeSpritemap`, `commerceCheckoutStep`,
`audiencesCustomAttributes`, `editorConfigContributor`. None of them hook into `DDMValidation`,
`DDMExpressionFunction`, or any other DDM/Data Engine backend extension point — same absence
confirmed separately for the actual field *editor* component registry (each DDM Form Field Type,
e.g. `Text.es.js` under `dynamic-data-mapping-form-field-type`, is a bundled portal OSGi module
JS resource with no CX-pluggable seam). Custom `DDMValidation` and `DDMExpressionFunction` components genuinely require a
traditional OSGi module (declarative JSON validation does not) — this is one of the few real cases (per this project's CLAUDE.md
escalation rule: "only suggest traditional OSGi modules if Client Extensions cannot fulfill the
requirements") where that escalation is justified rather than reached for by default.

A `globalJS` CX can add formatting, character counts, hints, conditional UI, or block
this UI's own submit; direct REST/JSONWS calls bypass all of that. Pair it with a
verified declarative/backend validator for an actual guarantee. DOM details deliberately
live only in the focused globalJS references:
- [Field selectors, hidden values, async mounts and observers](../../liferay-globaljs-editor-extension/references/field-dom-and-lifecycle.md).
- [Capture-phase submit blocking and CX boundaries](../../liferay-globaljs-editor-extension/references/submit-and-boundaries.md).
