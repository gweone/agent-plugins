---
name: liferay-globaljs-editor-extension
description: >
  Extend rendered DDM/Data Engine editors with a globalJS Client Extension: field selectors, hidden combobox values, async mounts, MutationObserver races, conditional UX and capture-phase Publish/Save blocking. Covers DLAdminPortlet screen detection and ERC lookup; browser-only, not backend validation.
---

# Liferay globalJS editor extension

Use for behavior layered onto an existing field editor, not replacing its
registered component. References retain live Document Library debugging lessons;
inspect other field types/forms rather than generalizing one observed DOM.

## Workflow

1. Resolve the current consuming workspace, local CX rules and target release.
   `client-extensions/liferay-global-extension` is an external example, not a
   prerequisite or plugin-local implementation.
2. Prefer one company-scoped globalJS registry: purpose-agnostic lifecycle engine,
   screen/entity adapter, then narrow purpose implementations.
3. Match `p_p_id` and namespaced `mvcRenderCommandName`; do not rely on
   `ThemeDisplay.isControlPanel()`. A missing render command is not exclusion.
4. Resolve entity IDs by ERC, cache per identifier including failed/null lookups,
   and negatively test filter parameters that might silently do nothing.
5. Inspect real markup; find controls with tag-restricted `ddm$$<fieldName>$`
   selectors and field containers with stable plain-name testing attributes.
6. Wait for async field mounts, guard late attachments with lifecycle tokens,
   and re-query replaced React subtrees from a stable server-rendered wrapper.
7. Debounce mutations and separately guard async re-entrancy; detach listeners
   and observers on deactivation.
8. Prefer native form rules when available; if the actual ask is to block this
   UI's submit, use scoped capture-phase interception, not a save-function patch.

## Critical constraints

- Bare substring selectors can match a label before the control and silently
  return undefined values. Restrict to `input`, `select`, `textarea`.
- A non-multiple select can be a combobox plus hidden JSON-array input; its
  React property updates need not fire `change`/`input`. Native radios differ.
- Mutation-heavy CKEditor/maps can pin the CPU; debouncing alone does not stop
  overlapping awaited activations. Treat both failure modes independently.
- Capture submit blocking is browser-only and depends on the actual submit path.
  Direct headless/JSONWS calls bypass every UX check here.
- No inspected CET type replaces the DDM editor registry or implements a backend
  `DDMValidation`/`DDMExpressionFunction` component.

## Focused references

- [Registry architecture, screen matching and ERC/filter pitfalls](references/registry-and-routing.md)
- [Selectors, hidden values, async lifecycle and observer code](references/field-dom-and-lifecycle.md)
- [Submit capture example, rejected monkey patch and CX limits](references/submit-and-boundaries.md)
- [Native dataRules and missing Rules tabs](../liferay-data-engine-form-rules/SKILL.md)
- [Backend validation guarantees](../liferay-ddm-field-validation/SKILL.md)
