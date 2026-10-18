# Submit interception and client-extension limits

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

## 8. Making a client-side check actually block a native-looking submit

A warning `<div>` next to a field is passive — it never stops a Publish/Save button. Two options
were considered for making it actually block submission, purely client-side (no backend change):

**Rejected: monkey-patching Liferay's own save function.** Portlets like `DLAdminPortlet` define
a namespaced global inline (`<namespace>saveFileEntry(draft)`) that a Publish button's form
`onSubmit` calls. Overriding `window['<namespace>saveFileEntry']` works today, but it's an
undocumented internal name that can change across versions, and — worse — can get silently
redefined if the portlet re-executes its inline `<script>` block on an AJAX re-render, undoing
the patch with no `activate()`/`deactivate()` transition to notice it by.

**Used instead: capture-phase `submit` interception.** A property-based handler
(`form.onsubmit = ...`, which is what an inline `onSubmit="..."` attribute becomes) always fires
*after* any capture-phase listener on an ancestor, per the DOM event spec. So:

```ts
document.addEventListener('submit', (event) => {
	const form = event.target as HTMLElement;
	if (!form.matches('[name="fm"]')) return;

	if (yourInvalidCondition) {
		event.preventDefault();
		event.stopImmediatePropagation(); // the framework's own onSubmit never runs
	}
}, {capture: true});
```

This is standard, version-independent DOM behavior — no dependency on Liferay's internal naming.
**Still purely client-side**, same limitation as everything else in this skill: it blocks the
UI's own submit button, not a direct headless/JSONWS call bypassing the UI entirely. Reach for
this specifically when "block this UI's own submit" is the actual ask; if the requirement must
hold for every client regardless of path, that's a backend concern — see [declarative backend validation](../../liferay-ddm-field-validation/references/declarative-validation.md).

**Before reaching for a client-side interception trick at all, check whether Data Engine's own
Form Rules (`dataRules` on the DataLayout) can do it instead** — `setRequired`-style rules are
evaluated entirely client-side by Data Engine's own JS, reusing its *native* required-field
UI/blocking rather than a hand-rolled one, which is generally the better result if it's
available. It usually isn't for a Document Type or Journal structure specifically
(`DataLayoutBuilderDefinition.allowRules()` defaults `false`; Document Library inherits
that value and Journal explicitly returns `false`, so the
admin builder UI never even offers a Rules tab to configure one) — see the
[form-rules reference](../../liferay-data-engine-form-rules/references/rules-and-grammar.md)
for the confirmed restriction and Form Rules expression syntax.

## 9. What a Client Extension categorically cannot do here

No registered `@CETType` (`fdsCellRenderer`, `fdsFilter`, `customElement`, `iframe`, `themeCSS`,
`globalJS`, `globalCSS`, `staticContent`, `themeFavicon`, `jsImportMapsEntry`, `themeSpritemap`,
`commerceCheckoutStep`, `audiencesCustomAttributes`, `editorConfigContributor` — checked
exhaustively) hooks into the DDM/Data Engine field-type registry, `DDMValidation`, or
`DDMExpressionFunction`. Everything a `globalJS` CX does here is DOM manipulation layered on top
of Liferay's own rendering, after the fact — never a replacement for the actual editor
component, and never backend-enforced. If the ask is genuinely "replace this field's editor with
a different widget" or "add a new reusable validator," that requires a traditional OSGi module —
see [custom validators](../../liferay-ddm-field-validation/references/custom-validators.md)
and [CX/backend boundaries](../../liferay-ddm-field-validation/references/backend-and-client-boundaries.md).

Observed DL detail: `edit_file_entry.jsp` uses the property-based handler
`onSubmit="event.preventDefault(); <namespace>saveFileEntry(...)"` (with a draft
argument in the original save function). The capture listener runs before this handler.
The sample `[name="fm"]` is illustrative: inspect the actual namespaced target form,
restrict interception to that form, and remove listeners on deactivation. It does not
prove interception of other programmatic save paths or all Data Engine forms.
