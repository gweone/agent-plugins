# Accessibility debugging (a11y)

Summarized from the upstream `a11y-debugging` skill. `take_snapshot` returns the
accessibility tree, which is what assistive tech sees, so it is the source of truth for
semantics, not the DOM or a screenshot. `opacity: 0` is still read by screen readers;
`display: none` and `aria-hidden="true"` are not.

## Order of checks

1. **Lighthouse baseline**: `lighthouse_audit` with `mode: "navigation"`. Scores are
   0-100 with `Passed`/`Failed` counts. The full `report.json` (path in the result) is
   huge; do not read it. Filter failures only:
   ```bash
   node -e "const r=require('<report.json>'); Object.values(r.audits).filter(a=>a.score!==null&&a.score<1).forEach(a=>console.log(JSON.stringify({id:a.id,title:a.title,items:a.details?.items})))"
   ```
   Omit `outputDirPath` for the temp dir, or point it inside the workspace.
2. **Browser-native issues**: `list_console_messages` with `types: ["issue"]` and
   `includePreservedMessages: true` (catches load-time issues such as missing labels and
   invalid ARIA).
3. **Structure**: `take_snapshot`; heading levels must not skip; DOM order must match the
   visual reading order (compare with `take_screenshot` to catch floats and absolute
   positioning that scramble the flow).
4. **Names and labels**: every button/input/image needs an accessible name (an icon-only
   button showing `""` fails); images need `alt`; find unlabeled inputs with the snippet
   below.
5. **Keyboard and focus**: `press_key` `Tab` / `Shift+Tab`, `take_snapshot`, find the
   focused element. A modal must pull focus in and trap it until closed, with no traps
   elsewhere.
6. **Tap targets**: at least 48x48 px with spacing; measure with `evaluate_script`
   passing the element `uid` (the snapshot has no sizes).
7. **Contrast**: WCAG AA is 4.5:1 normal text, 3:1 large text. The snippet is
   approximate (ignores transparency, gradients, background images); for text over
   images fall back to `take_screenshot` and a visual legibility call, or inject
   `axe-core` for a real audit.
8. **Document level**: `lang`, `title`, viewport meta (flag `user-scalable=no`),
   `prefers-reduced-motion`.

## Snippets (`evaluate_script`)

Unlabeled form inputs (no `label[for]`, `aria-label`, `aria-labelledby`, or wrapping label):

```js
() => Array.from(document.querySelectorAll('input, select, textarea'))
  .filter(i => !(i.id && document.querySelector(`label[for="${i.id}"]`))
    && !i.getAttribute('aria-label') && !i.getAttribute('aria-labelledby')
    && !i.closest('label'))
  .map(i => ({tag: i.tagName, id: i.id, name: i.name, placeholder: i.placeholder}));
```

Tap target size (pass the `uid` as the argument):

```js
el => { const r = el.getBoundingClientRect(); return {width: r.width, height: r.height}; }
```

Document-level checks:

```js
() => ({
  lang: document.documentElement.lang || 'MISSING',
  title: document.title || 'MISSING',
  viewport: document.querySelector('meta[name="viewport"]')?.content || 'MISSING',
  reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
})
```

For contrast, compute the WCAG ratio from `getComputedStyle(el).color` and
`backgroundColor` (relative luminance, `(L1+0.05)/(L2+0.05)`); treat the result as a
lead to verify, not proof.

## Reporting

List each failure with the element (selector or snapshot `uid`), the rule it breaks, and
the fix. Say which checks were automated and which were visual judgment. Guideline text:
append `.md.txt` to a web.dev article URL for clean markdown.
