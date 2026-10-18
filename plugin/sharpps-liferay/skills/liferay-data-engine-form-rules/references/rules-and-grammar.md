# Data Engine dataRules, grammar and builder restrictions

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

## 5. `dataRules` (show/hide, dependent-field UI rules) — real mechanism, but blocked for Document Types

`DataLayout.dataRules` (`actions`/`conditions`/`logicalOperator` — see
`DataRule.java` (`$LIFERAY_PORTAL/modules/apps/data-engine/data-engine-rest-api/src/main/java/com/liferay/data/engine/rest/dto/v2_0/DataRule.java`))
is the mechanism for show/hide/enable/disable/require-field rules between fields on the same
form — Data Engine's own Form Rules feature. Confirmed genuinely useful for "field B required
only when field A = X" **and** genuinely client-side-only (see the nuance at the end of this
section) — but there's a real access blocker specific to Document Types, found while trying to
use it.

### The exact JSON shape on `dataLayout.dataRules` is still unverified — but the underlying action/condition syntax now is

No populated `dataRules` fixture exists anywhere in the portal source tree, and a live PATCH test
to check the REST JSON syntax was correctly blocked by the harness (mutating a real resource just
to confirm shape needs explicit user permission first, even on a disposable resource) — so don't
hand-write a `dataLayout.dataRules` REST payload from a guessed shape.

What **is** now confirmed, from real non-test source (`DDMRESTDataProviderSettings.java`), is the
underlying expression/action syntax Form Rules are built from — the same DDM Expression Language
engine covers both this and declarative `validation` expressions. It's a **custom ANTLR4 grammar**
(`dynamic-data-mapping-expression` module's `DDMExpression.g4`), not MVEL/JEXL, evaluated by
`DDMExpressionImpl`/`DDMExpressionFactoryImpl`. Confirmed supported syntax: `&&`/`and`, `||`/`or`,
`not` (prefix only, no unary `!`), `==`/`!=`/`>`/`>=`/`<`/`<=`, `+ - * /`, parentheses, string/
number/boolean literals, array literals `[1,2,3]`, function calls, bare identifiers as field
references. **No `if/else`, no ternary `?:`** — it's expression-only. Real confirmed
cross-field example (a `@DDMFormRule` action string, referencing a *different* field):

```java
actions = {"setRequired('paginationStartParameterName', equals(getValue('pagination'), true))"}
```

`getValue('OtherField')` is the confirmed way to read another field from within a rule
expression — this is the annotation-based Java form, so whether the REST API's `dataLayout.
dataRules` JSON uses these same raw strings or wraps them into structured `actions: Map[]`/
`conditions: Map[]` objects is still the one open unknown. Get the real JSON shape one of two
ways, same as before — **but see the blocker below before reaching for method 1**:

1. Build one rule through the Control Panel's Data Layout designer UI (the drag-and-drop rule
   builder), then `GET /o/data-engine/v2.0/data-layouts/{id}` to read back the canonical JSON
   Liferay itself produced. **Does not work for Document Types or Journal (Web Content) —
   see below.** Works for the standalone Forms app.
2. Ask the user for explicit permission to test-PATCH a disposable/test data layout directly via
   the REST API (bypassing the missing UI), inspect the round-trip, then restore the original
   value. Untested whether the REST resource accepts/persists `dataRules` for
   `content.type=document-library` at all, or whether the runtime form renderer (a separate
   component from the builder) would honor it if present — a real next step if this matters.

### Document Types (and Journal) have no Rules builder UI at all — confirmed from source, not a discoverability issue

`DataLayoutBuilderDefinition.allowRules()` (default `false`,
`interface` (`$LIFERAY_PORTAL/modules/apps/data-engine/data-engine-taglib/`) —
per-`content.type` OSGi component) gates whether the Data Layout Builder's Rules sidebar panel
gets sent to the browser at all. `document-library-web`'s
`DocumentLibraryDataLayoutBuilderDefinition` (backing Document Type field editing,
`content.type=document-library`) never overrides it, so it inherits `false`. Confirmed in
`DataLayoutBuilderTag._getSidebarPanels()`: when the flag is off, the "rules" panel entry is
`null` — never rendered, not hidden behind an easy-to-miss button. `JournalDataLayoutBuilderDefinition`
(Web Content structures) explicitly sets it to `false` too. The standalone Forms app is the
exception — it doesn't even use this builder component; it uses an older, separate
`<ddm-form-builder>` taglib with rules hard-enabled (`initialConfigState.es.js`:
`allowRules: true`).

**Important nuance even once the real REST JSON shape is known:** `dataRules` show/hide/enable/
disable/require is evaluated **entirely client-side**, by Data Engine's own form JS — genuinely
useful as a front-end-only enforcement mechanism (it reuses Data Engine's native "required"
UI/blocking, not a hand-rolled one), but by itself never a backend guarantee, unlike declarative validation and custom validators. Confirmed: a `setRequired` rule does not touch the field's static `required` DB flag, so
`DDMFormValuesValidatorImpl` never sees it — a direct API call bypassing the UI sails through
untouched. If a field must actually be *required* regardless of client, express that as a
validation expression on the dependent field itself ([declarative validation](../../liferay-ddm-field-validation/references/declarative-validation.md)) — `dataRules` and declarative validation
expressions are not substitutes for each other; they enforce at different layers (UI vs. server)
and can be used together.

See [backend validation](../../liferay-ddm-field-validation/SKILL.md) for the enforcement layer;
its historical `if (...) { ... }` illustration is conceptual, not valid executable grammar.
