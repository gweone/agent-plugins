# globalJS registry, screen matching and ERC resolution

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

The original guidance came from building and live-debugging a Document Library
Document Type edit screen, rather than documentation alone. Several plausible
implementations failed until a live DOM sample exposed the difference. An optional
reference implementation in that earlier consuming workspace was
`client-extensions/liferay-global-extension/`, with `docs/README.md` and
`docs/usage.md` beneath it and a sample at
`src/extensions/documentType/managedDocument/`. Resolve equivalent paths in the
current application; these are not dependencies or local links in this plugin.

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
