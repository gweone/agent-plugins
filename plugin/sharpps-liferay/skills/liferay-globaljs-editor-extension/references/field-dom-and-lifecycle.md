# Rendered DDM field DOM and async lifecycle

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

## 4. Finding a rendered Data Engine field — confirmed attribute format, and a real collision bug

Data Engine renders a field's value-bearing control with an `id`/`name` containing
`ddm$$<fieldName>$<randomKey>$<repeatableIndex>$$<languageId>`, prefixed by the portlet namespace
and the containing structure's id — e.g.:

```
_com_liferay_document_library_web_portlet_DLAdminPortlet_39585_ddm$$dt_owner_email$Wep3VtS4$0$$en_US
```

Neither the structure-id prefix (unstable across re-imports, see [ERC resolution and recreated IDs](registry-and-routing.md)) nor the
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
on `change`/`input` for a field like this; react to DOM mutations instead (see [observer scheduling and re-entrancy](field-dom-and-lifecycle.md)), and
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
