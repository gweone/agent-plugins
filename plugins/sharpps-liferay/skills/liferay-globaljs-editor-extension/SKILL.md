---
name: liferay-globaljs-editor-extension
description: Use whenever the user wants to build a Client Extension that customizes a rendered Data Engine field editor from the browser — Document Types (DLFileEntryType), Objects, or any other Data-Engine-backed form (Forms app included). Trigger for "add UX to this field", "modify a field's editor without replacing it", "show/hide fields based on another field's selection", "add a live hint/format check to a field", "block the Publish/Save button on a condition", "why can't I find this field with querySelector", "globalJS client extension for a form", or any work building/debugging a `type: globalJS` Client Extension targeting `DLAdminPortlet`'s `edit_file_entry` screen or an analogous Data-Engine-rendered edit form. For backend/declarative validation (`DDMValidation`, `DDMExpressionFunction`, Form Rules internals) see the companion `liferay-ddm-field-validation` skill instead — that one is server-side, this one is the browser-side CX.
---

# Liferay globalJS Client Extension: Extending a Data Engine Field Editor

How to build a `type: globalJS` Client Extension that adds behavior to a rendered Data Engine
form — live hints, conditional show/hide, cross-field dependencies, even a blocked submit — all
purely client-side. Every pattern here was found by building and live-debugging one concretely
(a Document Library "Document Type" edit screen), not derived from documentation, and several
entries exist specifically because an earlier, plausible-looking version was wrong and only a
live DOM sample proved it. If a reference implementation exists in the current workspace, it's
usually at `client-extensions/liferay-global-extension/` (docs under `docs/README.md` and
`docs/usage.md` there go deeper on one concrete sample than this skill does) — treat this skill
as the portable lessons, not a dependency on that specific CX existing.

## 1. Why one CX, not one per purpose

`scope: company` on a `globalJS` CX means it loads on **every page of the instance**. Splitting
purposes across separate CXs multiplies cost for no benefit: N script tags, N copies of any
bundled runtime (nothing is shared between separate webpack bundles), N independent
`MutationObserver`s all firing on every mutation on every page. Use one CX with an internal
registry that dispatches to whichever purpose actually matches the current page, not N single-
purpose CXs.

### The layering that scales

```
Extension (root interface)         — purpose-agnostic: name, matches(), activate(), deactivate()
  └─ createXExtension() adapter     — wraps a narrower, purpose-built interface into Extension
       └─ YourNarrowerInterface     — e.g. "one Document Type's edit-screen customization"
```

The adapter is where screen detection, field-existence waiting, and value resolution belong —
keep the narrower interface simple (just `activate(container)`/`deactivate()`) so individual
purpose implementations don't each reinvent that plumbing. The root engine only ever calls
`matches()` → diff against a `Set` of active names → `activate()`/`deactivate()` on genuine
transitions; it has zero domain knowledge.

## 2. Detecting the right screen

Don't gate on `Liferay.ThemeDisplay.isControlPanel()` — a widget like `DLAdminPortlet` can be
embedded on an ordinary site page (dropped as a Widget), which renders the *same* portlet and
render command but is **not** `isControlPanel()` (that reflects whether the current layout
belongs to Liferay's special virtual Control Panel `Group`, a different thing from "is this
portlet instance the admin one"). Gate on the actual render-request query params instead, which
are identical in both contexts:

```ts
const params = new URLSearchParams(window.location.search);
const isTargetPortlet = params.get('p_p_id') === TARGET_PORTLET_ID;
const mvcRenderCommandName = params.get(`_${TARGET_PORTLET_ID}_mvcRenderCommandName`);
const isTargetScreen = !mvcRenderCommandName || mvcRenderCommandName === TARGET_RENDER_COMMAND;
```

Treat a missing `mvcRenderCommandName` param as "not excluded" rather than "not this screen" —
it's only present when explicitly set on a render request; its absence doesn't mean you're on a
different screen, just that the server used its default.

## 3. Resolving a Document Type (or any DDM-backed entity) id stably

Test/setup scripts that delete-and-recreate a Document Type/Object/structure on every run mean
its numeric primary key is **not stable** — never hardcode it. Resolve by
`externalReferenceCode` instead, and prefer JSONWS over headless REST for this specific lookup:

```ts
Liferay.Service(
	'/dlfileentrytype/fetch-file-entry-type-by-external-reference-code',
	{externalReferenceCode, groupId: Liferay.ThemeDisplay.getScopeGroupId()},
	callback
);
```

`headless-delivery`'s `/o/headless-delivery/v1.0/sites/{siteId}/document-data-definition-types`
looks like the "proper" REST way to do this, but its `filter` query param is a **silent no-op**
— confirmed: `BaseDocumentDataDefinitionTypeResourceImpl.getEntityModel` returns `null`, so
there's no `EntityModel` for the OData filter parser to translate `filter=` against. It's
accepted syntactically and does nothing — a filter for a value that doesn't exist still returns
every item, which looks like success until you test with a deliberately non-matching value.
**Always test a filter-looking query param with a value you know shouldn't match, not just one
that should** — that's the only way this kind of silent no-op surfaces.

Cache the resolved id **per identifier** (a `Map`), not in a single module-level variable — a
registry holding multiple such lookups (multiple Document Types, multiple structures) will
silently return the wrong id for every identifier but the first one resolved if the cache has
only one slot. Also cache a failed lookup (`null`) rather than leaving it eligible for retry
forever — otherwise every single DOM-mutation tick re-hits the network for something that will
never resolve.

## 4. Finding a rendered Data Engine field — confirmed attribute format, and a real collision bug

Data Engine renders a field's value-bearing control with an `id`/`name` containing
`ddm$$<fieldName>$<randomKey>$<repeatableIndex>$$<languageId>`, prefixed by the portlet namespace
and the containing structure's id — e.g.:

```
_com_liferay_document_library_web_portlet_DLAdminPortlet_39585_ddm$$dt_owner_email$Wep3VtS4$0$$en_US
```

Neither the structure-id prefix (unstable across re-imports, same reason as Section 3) nor the
trailing random-key/repeatable-index/locale suffix can be predicted — anchor a selector on the
one literal, stable substring: `ddm$$<fieldName>$`.

**A real bug this substring match causes if not tag-restricted:** "widget group" style fields —
anything using `aria-labelledby` for accessibility (a `select`-rendered-as-combobox, a checkbox
group, a radio group) — give their own `<label>` an `id` *also* containing that same
`ddm$$<fieldName>$` substring, for the label's own accessibility wiring:

```html
<label id="..._ddm$$dt_category$STfjlypb$0$$en_US_fieldLabel">Category</label>
...
<input name="..._ddm$$dt_category$STfjlypb$0$$en_US" type="hidden" value="[&quot;report&quot;]">
```

The label comes first in document order. A bare `[name*="ddm$$dt_category$"], [id*=...]`
selector (no tag restriction) matches the *label*, not the input — and a `<label>` has no
`.value` property, so every read silently resolves to `undefined`. Symptom in practice: a
computed condition that always evaluates as if the field were empty, no matter its real value,
and — worse — if anything reacts to that (e.g. re-hiding something whenever it recomputes), it
looks like the fix keeps getting "reverted" within a frame, because the very next scheduled
recompute runs against the label again. **Fix: restrict the selector to actual form-control tag
names.**

```ts
function buildFieldSelector(fieldName: string): string {
	const marker = `ddm$$${fieldName}$`;

	return ['input', 'select', 'textarea']
		.flatMap((tag) => [`${tag}[name*="${marker}"]`, `${tag}[id*="${marker}"]`])
		.join(', ');
}
```

Fields not using `aria-labelledby` (plain `for=`-labeled text/date/color fields) never had this
problem — which is exactly why it can hide for a while: three other fields worked fine with the
untagged selector before a "widget group" field exposed it.

### A separate, more stable lookup for the field's *container*

The field's outer wrapper carries a stable, plain-field-name attribute, present identically
across every field type observed (they share Data Engine's `FieldBase` component) — prefer this
over guessing a wrapper's CSS class:

```html
<div class="ddm-field-container ddm-target h-100" data-field-name="dt_reference">
  <div class="ddm-field" data-field-name="dt_reference" data-qa-id="dt_reference">
    <div class="form-group" data-field-name="<namespaced-encoded-name>" data-field-reference="dt_reference">
```

`[data-qa-id="<plain field name>"]` is Liferay's own stable testing-selector convention —
use it for "find the whole field's container to hide/show/highlight," and the `ddm$$` marker
(above, tag-restricted) for "find the actual control to read/write its value."

## 5. Fields aren't rendered synchronously — wait, don't assume

Data Engine fetches and mounts its fields via its own separate async process, which can finish
*after* whatever triggered your extension's `activate()` already resolved (e.g. a document-type
match on a sibling field). If `activate()` does a one-shot synchronous lookup and finds nothing
because the field genuinely isn't in the DOM yet, and `activate()` only fires once per
inactive→active transition, the enhancer never gets a second chance — it silently gives up
forever for that activation, even though the field appears moments later.

Fix: make the lookup resolve immediately if the field already exists, otherwise wait via a
`MutationObserver` scoped to the narrowest reasonable ancestor (not `document.body` — if the
engine already runs its own top-level observer, don't add a second one watching the whole page)
until the field appears or a timeout elapses:

```ts
function waitForSelector<T extends HTMLElement>(
	selector: string, root: Document | Element, timeoutMs: number
): Promise<T | null> {
	const existing = root.querySelector<T>(selector);
	if (existing) return Promise.resolve(existing);

	return new Promise((resolve) => {
		const cleanup = () => { observer.disconnect(); clearTimeout(timeoutId); };
		const observer = new MutationObserver(() => {
			const field = root.querySelector<T>(selector);
			if (field) { cleanup(); resolve(field); }
		});
		const timeoutId = setTimeout(() => { cleanup(); resolve(null); }, timeoutMs);
		observer.observe(root, {childList: true, subtree: true});
	});
}
```

This makes every "attach behavior to field X" function async. That introduces a real race your
purpose's `deactivate()` must guard against: it can now run *before* an in-flight attach resolves
(user switches away before fields finish rendering). Guard with a token incremented on every
activate/deactivate; when a late-resolving attach's token no longer matches current, detach
immediately instead of keeping it — otherwise you leak listeners onto a screen you've already
left.

## 6. Don't assume a field type renders as its "obvious" native element

A `select` (non-`multiple`) Data Engine field is **not** a native `<select>` — it renders as a
custom combobox (a `<button role="combobox">` for display) backed by a hidden `<input>` holding
the real value as a **JSON-encoded array string**, e.g. `'["report"]'`, even though the field
isn't `multiple`. A plain string comparison against `.value` will never match; parse it:

```ts
function getSelectedValues(control: HTMLInputElement): string[] {
	try {
		const parsed = JSON.parse(control.value || '[]');
		return Array.isArray(parsed) ? parsed : [String(parsed)];
	}
	catch {
		return control.value ? [control.value] : [];
	}
}
```

Separately: because Data Engine (React) updates that hidden input's `.value` **property**
programmatically rather than through direct user interaction with the input itself, a plain
`change` event listener on it does not reliably fire — confirmed live, not a maybe. Don't rely
on `change`/`input` for a field like this; react to DOM mutations instead (see Section 7), and
re-read the value fresh each time rather than trusting a value captured once.

**General lesson, not specific to `select`:** verify a field's real rendered markup before
writing a selector or reading its value — checkboxes and radios in this same system *do* render
as genuine native `<input type="checkbox|radio">` and *do* fire real `change` events, so the
right approach differs per field type. Don't generalize from one confirmed field to "all fields
work this way."

## 7. Any MutationObserver you attach needs debouncing — and the engine needs re-entrancy protection too, separately

Two distinct bugs, easy to conflate, found in this order:

**7a. A `MutationObserver` callback that isn't debounced can pin the CPU with no thrown
exception — no console error, just something that looks exactly like an unrelated hang.**
If your observer's root includes a rich text editor or a map widget (CKEditor, Leaflet, anything
similarly DOM-mutation-heavy), those generate mutation volume on a completely different order of
magnitude from a typical form field, continuously, on their own, unrelated to anything you care
about — cursor blink, tile loading, focus state. Worse, if your callback's own writes (e.g.
toggling a class) land inside the observed subtree, they can register as further mutations for
the same observer to react to. Debounce via `requestAnimationFrame` + a boolean flag, collapsing
any burst into at most one real callback per frame:

```ts
let scheduled = false;
function scheduleUpdate() {
	if (scheduled) return;
	scheduled = true;
	requestAnimationFrame(() => { scheduled = false; update(); });
}
```

**7b. Separately, an async `apply()`/tick function needs a re-entrancy guard, not just a
debounced trigger.** Debouncing limits how often a *new* call gets scheduled — it says nothing
about a *previous* call's async work (e.g. an awaited network lookup) still being in flight.
Under the same mutation-heavy-widget conditions as 7a, several calls can overlap; each one reads
shared "is X currently active" state as still unset, because none of the earlier in-flight calls
have reached their `.then()` yet to update it — so *every one* independently activates something
that should only activate once. Symptom: a DOM insertion meant to happen once ends up duplicated
several times over, all with correct/consistent content (which makes it look more confusing than
a typical bug, since nothing is *wrong*, just multiplied). Fix with a running flag that doesn't
drop a call that arrives mid-flight, but defers it to run once more right after:

```ts
let running = false, rerunNeeded = false;
function apply() {
	if (running) { rerunNeeded = true; return; }
	running = true; rerunNeeded = false;
	doAsyncWork().finally(() => {
		running = false;
		if (rerunNeeded) apply();
	});
}
```

Fix 7a and 7b independently — a project can have one without the other, and they present almost
identically ("something's clearly wrong but no error anywhere") until you inspect which layer is
actually re-entering.

**7c. When re-querying to avoid a stale reference, re-query from a genuinely stable root.**
If Data Engine replaces a field's DOM subtree wholesale on a state change (a React re-render, not
an in-place mutation) rather than mutating it, a `MutationObserver`/reference attached to that
specific subtree goes stale — it stops seeing anything, even though the live field keeps
changing elsewhere in a freshly-created replacement node. The reliably-stable root to re-query
from is whatever static, JSP/server-rendered wrapper contains the whole form (never replaced by
React) — not any specific field's own container.

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
hold for every client regardless of path, that's a backend concern — see the companion
`liferay-ddm-field-validation` skill, Section 2.

**Before reaching for a client-side interception trick at all, check whether Data Engine's own
Form Rules (`dataRules` on the DataLayout) can do it instead** — `setRequired`-style rules are
evaluated entirely client-side by Data Engine's own JS, reusing its *native* required-field
UI/blocking rather than a hand-rolled one, which is generally the better result if it's
available. It usually isn't for a Document Type or Journal structure specifically
(`DataLayoutBuilderDefinition.allowRules()` defaults `false` and neither overrides it, so the
admin builder UI never even offers a Rules tab to configure one) — see the
`liferay-ddm-field-validation` skill, Section 5, for the confirmed restriction and the Form
Rules expression syntax.

## 9. What a Client Extension categorically cannot do here

No registered `@CETType` (`fdsCellRenderer`, `fdsFilter`, `customElement`, `iframe`, `themeCSS`,
`globalJS`, `globalCSS`, `staticContent`, `themeFavicon`, `jsImportMapsEntry`, `themeSpritemap`,
`commerceCheckoutStep`, `audiencesCustomAttributes`, `editorConfigContributor` — checked
exhaustively) hooks into the DDM/Data Engine field-type registry, `DDMValidation`, or
`DDMExpressionFunction`. Everything a `globalJS` CX does here is DOM manipulation layered on top
of Liferay's own rendering, after the fact — never a replacement for the actual editor
component, and never backend-enforced. If the ask is genuinely "replace this field's editor with
a different widget" or "add a new reusable validator," that requires a traditional OSGi module —
see the `liferay-ddm-field-validation` skill, Sections 3 and 4, for exactly which extension
points those require and why no CX substitute exists.
