---
name: html-to-datasource
description: Use when a rendering's `.cshtml` has wording, validation rules/messages, option lists, or links hardcoded directly in the markup, and it needs to become a real Sitecore-driven component - authors edit it through Content Editor/Experience Editor instead of a developer editing HTML. Covers reading hardcoded HTML/markup to classify every literal into a field (wording vs. parameter vs. option-list vs. link), grouping fields into Template Sections rather than a flat field list, the Shared-field rule for non-translatable parameters (no per-language instance), a repeatable-option-list pattern for things like dropdown/checkbox choices, per-language Standard Values defaults for every supported language, detecting whether the rendering must be a View Rendering or Controller Rendering from how it's actually invoked and wiring its Datasource Template/Datasource Location fields, and the mandatory design-plan approval gate (template path, datasource path, rendering type, and field/standard-value design) before anything is created in Sitecore. This is solution-agnostic guidance, not tied to any specific SharpPS solution's naming or content. Builds on top of the `sitecore` skill's template/rendering/datasource creation mechanics (SPE, paths, sections/fields) rather than duplicating them - read that skill first if unfamiliar with it.
---

# Converting hardcoded HTML into a Sitecore-driven datasource

Scope: turning a rendering whose `.cshtml` hardcodes real content (copy,
validation thresholds/messages, option lists, links) into one backed by a
proper Sitecore datasource template, so every one of those values becomes
editable in Sitecore instead of living in markup. This is **generic guidance
for any SharpPS Sitecore solution** - it deliberately contains no
solution-specific naming, wording, or business content; adapt the patterns
below to whatever component you're actually converting.

This skill assumes the `sitecore` skill's CMS workflow (template/rendering/
datasource paths, `New-SPESession` + `Invoke-RemoteScript` mechanics,
`Add-ItemTemplateSection`/`Add-ItemTemplateField`) as its execution engine -
it is not repeated here. Read that skill first.

## Workflow: Spec -> Template Design Plan (needs approval) -> Execution

**Spec - ask the user if any of this is missing, don't guess:**
- The source `.cshtml` (or plain HTML) to convert - existing file path.
- Tenant/Site, Feature name, rendering name (same as the `sitecore` skill's
  spec items).
- How this rendering actually gets invoked, so its type (View vs.
  Controller) can be *detected* rather than guessed - see the detection
  procedure in Step 7 below; only fall back to asking the user when the
  codebase evidence is genuinely ambiguous.
- Whether repeatable option lists (dropdown choices, checkbox groups, card
  lists, etc.) should be author-managed child items in the content tree, or
  are stable enough to leave as static markup - don't assume every
  hardcoded list must become data-driven; confirm which ones the user
  actually wants editable.
- Whether the Feature project this belongs to already exists - if not, see
  the `feature-foundation-project` skill first.
- **Which languages the target Tenant/Site actually supports.** Needed to
  know how many Standard Values language versions to create (see Step 6) -
  don't assume single-language; ask rather than defaulting to whatever
  language the original HTML happens to be written in.
- **The exact template path and datasource item path to use.** The
  `sitecore` skill's `{core}`/`{area}`/`{featurename}`/`{renderingname}`
  convention only produces a *default* - always state the resolved path
  back to the user and get it explicitly confirmed (Tenant/Site included)
  before it goes into the design table below. Never silently create at a
  derived path without that confirmation, since a wrong template or
  datasource location is exactly as expensive to fix after the fact as a
  wrong field design.

**Plan - build the template design, then get explicit approval before
creating anything (see "Approval gate" below):**
1. Walk the HTML and classify every hardcoded literal (see "Step 1" below).
2. Turn that classification into a field list grouped into Sections (see
   "Step 2" and "Step 3").
3. Decide each field's sharing (Shared vs. per-language) using the
   parameter rule (see "Step 4").
4. Decide which lists need the repeatable-option-item pattern (see
   "Step 5").
5. Decide the Standard Values default for every field, per supported
   language for anything not Shared (see "Step 6").
6. Detect whether the rendering must be a View Rendering or a Controller
   Rendering, and resolve its `Datasource Template`/`Datasource Location`
   values (see "Step 7").
7. Present the full design - **confirmed template path, confirmed
   datasource item path, the sections/fields/types/sharing table, the
   per-language Standard Values, and the rendering type + Datasource
   Template/Location** - to the user and get explicit approval - **do not
   create the template or rendering speculatively and adjust after the
   fact.**

**Execution (only after approval):**
1. Create the template/sections/fields, rendering, and datasource item
   exactly as approved, using the `sitecore` skill's SPE mechanics and path
   conventions.
2. Create the template's `__Standard Values` item and populate it exactly
   as approved - the Shared defaults once, and a language version per
   supported language for every Unversioned/Versioned field (see Step 6).
3. Create the rendering item as the type detected in Step 7 (View or
   Controller), with `Datasource Template` and `Datasource Location` set
   to the template/datasource paths from this same run (see Step 7).
4. Rewrite the `.cshtml` to read every converted value from the datasource
   instead of the literal (see "Rewiring the .cshtml" below).
5. Report back the template/rendering/datasource paths and confirm the
   rewritten markup renders the same output when the datasource is
   populated with the original hardcoded values (a no-op visual diff is the
   correctness check).

## Step 1: Extract the configurable surface from the HTML

Read through the markup and classify every hardcoded literal into one of
these buckets - don't skip straight to writing fields without doing this
pass explicitly, since it's what the Section/sharing decisions in later
steps are based on:

| Bucket | What it looks like in HTML | Example |
|---|---|---|
| **Wording** | Visible text, `placeholder`, `aria-label`, button labels | Headings, field labels, button text, disclaimer copy |
| **Validation parameter** | A numeric/boolean constraint baked into markup or a data-attribute | `min="30" max="70"`, a `required` attribute, a step value |
| **Validation message** | User-facing text shown when a rule fails | `data-error-required="..."`, `data-error-max="..."` |
| **Option list** | A repeated block of choices (`<option>`-like items, checkbox groups, card lists) | A dropdown's list of selectable values, a checkbox group's items |
| **Link/CTA** | A hardcoded `href`, target URL, or link text | A "Learn more" link currently pointing at `#` |
| **Structural markup** | Wrapper `div`s, CSS classes, `data-component`/`data-role` JS hooks, icons | Layout scaffolding, JS behavior hooks, decorative icons |

**Only the first five buckets become Sitecore fields.** Structural markup
stays in the `.cshtml` as-is - don't turn CSS classes, JS hooks, or layout
wrappers into fields unless the user explicitly asks for visual/structural
variability (that's a Rendering Variant concern, not a datasource-field
concern - out of scope here).

## Step 2: Map each bucket to a field type

| Bucket | Sitecore field type | Notes |
|---|---|---|
| Wording (short) | Single-Line Text | Labels, button text, short headings |
| Wording (long/formatted) | Rich Text | Disclaimers, paragraph copy |
| Validation parameter (numeric) | Integer / Number | Min/max/step/threshold values |
| Validation parameter (boolean) | Checkbox | e.g. "Is Required" |
| Validation message | Single-Line Text | One field per distinct rule (required/min/max/etc.), not one shared message field |
| Option list | Child items under a sub-template (see Step 5) | Not a delimited string field - each option needs its own editable value/label |
| Link/CTA | General Link | Never a plain text field for something that's actually a link |

## Step 3: Group fields into Sections - never a flat field list

Every template built from this workflow must organize its fields into
**Template Sections** (`Add-ItemTemplateSection`, per the `sitecore`
skill's example), grouped by what the fields describe - not left as one
flat list under a single default section. Pick section names that match the
component's own conceptual grouping, e.g.:

- `Content` / `Copy` - headings, subtitles, disclaimer text
- `Validation` - one section per form field's parameters+messages, or a
  single `Validation` section if the component only has a couple of rules
- `Options` - the repeatable-list container reference (Step 5)
- `Links` - CTA/link fields
- `Result` / `Display` - labels used only in an output/result area, if the
  component has one

A component with several distinct form fields (each with its own
label/placeholder/validation) reads better as **one section per form
field** (e.g. `Field: Amount`, `Field: Term`) rather than lumping every
field's label with every other field's validation message under one
generic `Validation` section - group by what a content author is editing
at once, not by field type alone.

## Step 4: The Shared-field rule - parameters have no per-language instance

Decide each field's **Field Sharing** using what kind of value it holds,
not just where it appeared in the HTML:

| Field nature | Sharing | Reasoning |
|---|---|---|
| Wording/label/message shown to a visitor | **Unversioned** (default) or **Versioned** if it must vary per content version | Translatable copy - genuinely needs a per-language instance |
| Validation parameter (min/max/step/threshold/required-flag, internal key) | **Shared** | Not translatable text - one value across every language and version, so no per-language instance should exist at all |
| Link/reference | Unversioned if the link text/target differs by language, Shared if it's a purely internal/technical reference | Judge by whether the *value itself* is language-dependent |

In short: **if a field's value is a parameter/constraint rather than
user-facing wording, mark it Shared** - creating separate language
instances for a number like `max="5000000"` or a boolean like `required`
is never correct, since the value doesn't change by language.

Standard SPE template-field creation supports this via switches on
`Add-ItemTemplateField` (e.g. `-Shared`, `-Unversioned`) - this is standard
SPE cmdlet behavior, not independently verified against every SPE version,
so confirm the exact parameter names with `Get-Help Add-ItemTemplateField
-Full` on the target instance before running the creation script.

## Step 5: Repeatable option lists - child items, not a delimited field

A hardcoded list of choices (dropdown options, checkbox-group items, card
lists) should become **child items under a sub-template**, not a single
field with a delimited string value - each option needs its own editable
label/value pair, its own ordering (item sort order), and the ability for
an author to add/remove options without a code change.

Pattern:
1. A small sub-template (e.g. `{RenderingName} Option`) with fields for
   whatever varies per option - typically `Value` (Shared - it's an
   internal key, not wording) and `Label` (Unversioned - it's displayed
   wording).
2. The option items live as children of the datasource item itself (or a
   folder under it, if the datasource also needs its own non-list fields)
   - no separate path convention needed beyond the `sitecore` skill's
     existing datasource item path.
3. The `.cshtml` iterates `datasource.Children.Where(c => c.TemplateID ==
   optionTemplateId)` (ordered by Sitecore's item sort order) instead of
   looping over a hardcoded array.

Only apply this pattern to lists the user actually wants author-editable
(confirmed in Spec) - a list that's effectively fixed (e.g. tied to a
backend enum the code depends on) may be better left as static markup or a
Droplink to a shared, developer-managed list elsewhere, rather than forcing
every hardcoded list through this pattern regardless of whether it needs to
change.

## Step 6: Standard Values - a default per supported language

Every template built from this workflow needs a `__Standard Values` item
(Sitecore's built-in fallback-content item for anything created from that
template) populated with real defaults - not left blank - so a newly
inserted datasource item shows sensible content in Content
Editor/Experience Editor immediately, and so the original component still
renders correctly even before an author has touched it.

- **Shared fields** (Step 4): one default value on the Standard Values
  item itself - no per-language version needed, consistent with a Shared
  field having no per-language instance in the first place. This is where
  the original hardcoded parameter (e.g. `min="30"`, `max="70"`) belongs.
- **Unversioned/Versioned fields** (wording, messages): a **Standard
  Values language version for every language confirmed in Spec**, each
  with its own default text for that language - not just the language the
  original HTML happened to be written in. If translated copy isn't
  available yet for a given language, use an explicit placeholder (e.g.
  `"[Translate: Heading]"`) rather than leaving it blank or silently
  reusing another language's text - a blank/borrowed default is easy to
  mistake for "already translated."
- **Option sub-template items** (Step 5) get their own Standard Values the
  same way, if the sub-template itself needs sensible per-language
  defaults for authoring a brand-new option.

Standard SPE pattern for creating and populating it (same verification
caveat as Step 4 - confirm exact cmdlet/property names with `Get-Help` on
the target instance before running):

```powershell
$standardValues = New-Item -Path $template.ItemPath -Name "__Standard Values" -ItemType $template.ID
$template.Editing.BeginEdit()
$template.Fields["__Standard values"].Value = $standardValues.ID.ToString()
$template.Editing.EndEdit() | Out-Null

# Shared field defaults - set once, no language loop
$standardValues.Editing.BeginEdit()
$standardValues["MinValue"] = "30"
$standardValues["MaxValue"] = "70"
$standardValues.Editing.EndEdit() | Out-Null

# Unversioned/Versioned field defaults - one version per supported language
foreach ($languageName in $SupportedLanguages) {
    $language = [Sitecore.Globalization.Language]::Parse($languageName)
    $languageItem = Get-Item -Path $standardValues.ID -Language $language
    if ($languageItem.Versions.Count -eq 0) { $languageItem = $languageItem.Versions.AddVersion() }
    $languageItem.Editing.BeginEdit()
    $languageItem["Heading"] = $DefaultsByLanguage[$languageName]["Heading"]
    $languageItem["ErrorRequiredMessage"] = $DefaultsByLanguage[$languageName]["ErrorRequiredMessage"]
    $languageItem.Editing.EndEdit() | Out-Null
}
```

Include the resolved per-language defaults in the design-plan table the
user approves (Step 6 column below) - decide them as part of the plan, not
improvised during execution.

## Step 7: Create the rendering - detect View vs. Controller, wire Datasource Template/Location

The datasource template alone isn't enough - the rendering item that
points authors at it has to exist too, and its type isn't a coin flip:
**detect** it from how the component is actually invoked, per the
`sxa-cshtml-controller-rendering` skill.

**Detection procedure - check these in order, don't default to View
Rendering without checking:**
1. Search the codebase for how the `.cshtml` (or the rendering item it
   will replace, if converting an existing one) is actually reached:
   - Assigned to a page's placeholder through normal Sitecore/SXA layout
     (Content Editor's Presentation Details / Experience Editor's
     "Insert component") -> reached through the standard page-rendering
     pipeline -> **View Rendering** is fine.
   - Referenced as a Rendering Variant's Component Variant Field (e.g. the
     `sxa-search` skill's search-result variants), invoked from a Web API
     controller, a background job, or anywhere else outside a normal page
     request -> **must be a Controller Rendering** - a View Rendering
     there is fragile and can throw `InvalidOperationException: ViewContext
     from empty stack` (see that skill for the full why).
2. If evidence from step 1 is genuinely ambiguous (e.g. a brand-new
   component with no existing call site to inspect), ask the user rather
   than guessing - but exhaust the codebase search first; don't ask when
   the invocation path is already visible in the code.

**Wiring the rendering item (either type):**

| Field | View Rendering | Controller Rendering |
|---|---|---|
| Template | `/sitecore/templates/System/Layout/Renderings/View Rendering` | `/sitecore/templates/System/Layout/Renderings/Controller rendering` (`{2A3E91A0-7987-44B5-AB34-35C2D9DE83B9}`) |
| View/controller wiring | `Path` = the `.cshtml`'s virtual path | `Controller` = `Sitecore.XA.Foundation.Mvc.Controllers.StandardController, Sitecore.XA.Foundation.Mvc`, `Controller Action` = `Index`, `RenderingViewPath` = the `.cshtml`'s virtual path (see the `sxa-cshtml-controller-rendering` skill - reuse the existing `StandardController`, don't write a new one) |
| **`Datasource Template`** | the template item created in Steps 2-6, by ID | same |
| **`Datasource Location`** | the datasource item's parent folder path (the `sitecore` skill's `{sxa-site}/Data/{core}/{area}/{featurename}/{renderingname}` path) | same |

Setting `Datasource Template`/`Datasource Location` on the rendering item
is what makes Content Editor's "Insert options" and the datasource picker
offer the right template/location automatically - without them, an author
inserting this component has to know the template/path by hand.

```powershell
$rendering = New-Item -Path $renderingFolder -Name $RenderingName -ItemType $renderingTemplateId  # View or Controller template ID above
$rendering.Editing.BeginEdit()
$rendering["Datasource Template"] = $template.ID.ToString()
$rendering["Datasource Location"] = $dataFolder.ID.ToString()
if ($isControllerRendering) {
    $rendering["Controller"] = "Sitecore.XA.Foundation.Mvc.Controllers.StandardController, Sitecore.XA.Foundation.Mvc"
    $rendering["Controller Action"] = "Index"
    $rendering["RenderingViewPath"] = $cshtmlVirtualPath
} else {
    $rendering["Path"] = $cshtmlVirtualPath
}
$rendering.Editing.EndEdit() | Out-Null
```

## Approval gate: the template design must be approved before creation

Template shape is expensive to change once a component is live - renaming
or restructuring fields after authors have entered content means a
migration, not just an edit. So:

- Present **the confirmed template path, the confirmed datasource item
  path, the detected rendering type (View or Controller) with the
  evidence for it, the resolved `Datasource Template`/`Datasource
  Location` values, and** the design as a table (Section -> Field -> Type
  -> Sharing -> Standard Value(s)) covering every field decided in
  Steps 2-6, before writing or running any SPE creation script. Path,
  rendering type, field design, and Standard Values defaults are approved
  together, as one package - a path confirmed once in Spec still gets
  restated here, since it's part of what's being approved, not a separate
  earlier step to skip past.
- Include a short rendering summary alongside the field table:

  | Rendering type | Why (evidence) | Datasource Template | Datasource Location |
  |---|---|---|---|
  | Controller | invoked via a Component Variant Field in a search-result variant | `{template ID from Steps 2-6}` | `{datasource item parent path}` |
- Get the user's explicit approval on that table. If working in an
  interactive session, this is exactly what Claude Code's Plan Mode is
  for - use it so the design is reviewed and approved as a discrete step,
  not folded silently into execution.
- Only after approval, move to Execution and create the template exactly
  as approved - don't create a first draft in Sitecore and iterate on it
  live; iterate on the design table instead.

**Required table format** - `Section`/`Name`/`Type`/`Shared` always as one
row per field, grouped/ordered by Section (option sub-template fields
listed as their own mini-table right after the section that references
them). A **Shared** field gets one `Standard Value` column; a non-Shared
field gets one `Standard Value` column *per supported language* instead
(shown here for two example languages - use however many were confirmed in
Spec):

| Section | Name | Type | Shared | Standard Value (en) | Standard Value (id) |
|---|---|---|---|---|---|
| Content | Heading | Single-Line Text | No | "Plan it with us" | "Wujudkan rencana Anda" |
| Content | Disclaimer | Rich Text | No | "This is a simulation only." | "Simulasi ini hanya ilustrasi." |
| Field: Amount | Label | Single-Line Text | No | "Amount" | "Jumlah" |
| Field: Amount | Placeholder | Single-Line Text | No | "Enter amount" | "Masukkan jumlah" |
| Field: Amount | MinValue | Integer | **Yes** | `100000000` (single value, no per-language columns) | |
| Field: Amount | MaxValue | Integer | **Yes** | `5000000000` (single value, no per-language columns) | |
| Field: Amount | ErrorRequiredMessage | Single-Line Text | No | "Amount is required" | "Jumlah wajib diisi" |
| Field: Amount | ErrorMaxMessage | Single-Line Text | No | "Maximum 5,000,000,000" | "Maksimal Rp5.000.000.000" |
| Options | (child items, see Option sub-template below) | - | - | - | - |
| Links | PrimaryCta | General Link | No | (link target/text, per language) | |

*Option sub-template* (only if Step 5 applies):

| Section | Name | Type | Shared | Standard Value (en) | Standard Value (id) |
|---|---|---|---|---|---|
| Data | Value | Single-Line Text | **Yes** | `"option-1"` (single value) | |
| Data | Label | Single-Line Text | No | "Option 1" | "Opsi 1" |

This is the literal shape to fill in and show the user for every
conversion - not a format to paraphrase into prose. A Shared row's
Standard Value spans/collapses to one column since it has no per-language
instance (Step 4); leave the other language columns blank rather than
repeating the same value in each.

## Execution: reuse the `sitecore` skill - don't reinvent the mechanics

Once the design is approved, follow the `sitecore` skill's "CMS
content-tree conventions" workflow verbatim for the actual creation:
- Datasource template path, rendering path, datasource item path (same
  `{core}`/`{area}`/`{featurename}`/`{renderingname}` convention).
- `New-SPESession` + `Invoke-RemoteScript`, one session for
  template+sections+fields+rendering+datasource+options, not several.
- `Add-ItemTemplateSection` per Section from Step 3, then
  `Add-ItemTemplateField` per field from Steps 2/4 under the right section
  (adding the Shared/Unversioned switch decided in Step 4).
- Create the rendering item as detected/approved in Step 7, with
  `Datasource Template`/`Datasource Location` set to this run's template
  and datasource paths.
- Create the `__Standard Values` item and populate it per Step 6, in the
  same `Invoke-RemoteScript` session as everything else above.

## Rewiring the `.cshtml` to read fields instead of literals

Replace each literal identified in Step 1 with a read from the datasource
item, keeping structural markup untouched:

```cshtml
@{
    Item datasource = RenderingContext.Current.Rendering.Item;
}
<h2>@Html.Sitecore().Field("Heading", datasource)</h2>
<input type="text"
       min="@datasource["MinValue"]"
       max="@datasource["MaxValue"]"
       data-error-required="@datasource["ErrorRequiredMessage"]"
       data-error-max="@datasource["ErrorMaxMessage"]" />

@foreach (var option in datasource.Children.Where(c => c.TemplateID == optionTemplateId))
{
    <option value="@option["Value"]">@Html.Sitecore().Field("Label", option)</option>
}
```

- Use `Html.Sitecore().Field(...)` (not raw `datasource["Field"]`) for any
  field an author might edit in Experience Editor, so inline/WYSIWYG
  editing keeps working - reserve the raw indexer for non-rendered values
  like validation parameters that never need Experience Editor click-to-
  edit.
- After rewiring, verify the component renders identically when the
  datasource is populated with the original hardcoded values - that's the
  correctness check for the conversion, not just "it compiles."

## Related skills

- `sitecore` - the template/rendering/datasource creation mechanics this
  skill builds on; read it first.
- `sxa-cshtml-controller-rendering` - if the converted component must work
  outside a normal page-rendering pipeline request.
- `feature-foundation-project` - if the Feature project the component
  belongs to doesn't exist yet.
- `sxa-search` - if the component being converted is a search-result
  Rendering Variant rather than a standalone rendering.
