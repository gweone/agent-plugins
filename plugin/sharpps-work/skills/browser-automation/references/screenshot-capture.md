# Screenshot capture

Capture the real running app, not a mockup. The capture logic works across Windows, macOS
and Linux; dependency setup and credential-file encoding need care
([setup](setup.md), [auth and state](auth-and-state.md)).

## Approach

- Use an isolated context and separate role state files; log in as described in
  [auth and state](auth-and-state.md).
- For a local virtual host, navigate with the real hostname and a Chromium resolver rule
  ([setup](setup.md#reaching-a-local-multi-tenant-or-reverse-proxied-instance)).
- Scope selectors to the intended visible container. Strict locator actions may throw on
  multiple matches; choosing `.first()` can instead hide an ambiguity.

## Selector robustness: pitfalls that cause silently-wrong captures

- **Never use a bare `page.click('text=...')` for common words** ("Create", "Save", "Edit")
  on a page with a sidebar/nav. It can match an unrelated element elsewhere on the page and
  navigate somewhere completely different, and the script won't error, it'll just
  screenshot the wrong page. Scope the selector to the actual toolbar/container:
  `page.locator('.page-actions button:has-text("Create")')`.
- **When a locator resolves to multiple elements**, strict locator actions such as
  `locator.click()` may throw; non-strict legacy selector actions or explicit `.first()` can
  target an unintended match. Dropdown menus commonly render hidden duplicates. Prefer a
  selector that resolves to exactly one intended, visible element; use `.first()`/`.last()`
  only as a last resort with an explicit visibility check.
- **In a repeating grid/table**, target rows by an explicit index attribute
  (`[data-idx="1"]` or the app's equivalent), not `.first()`/`.last()`. Adding or removing a
  row during the same flow silently shifts what `.last()` now refers to, and a script that
  "worked" can start filling the wrong row after an earlier step changed the row count.
- Generic form-level errors (for example "quantity cannot be zero", "field X is mandatory")
  often fire *before* the specific validation actually being documented. If a capture keeps
  hitting the wrong error dialog, check what other mandatory fields the form needs filled
  first before the intended validation path is even reached.

## Review loop

Iterate by capturing a screenshot after every meaningful step and **actually reading it
back** before trusting the script succeeded. A script exiting 0 only means no exception was
thrown, not that the right thing is on screen (a wrong click can silently land on an
unrelated page). This is the fastest way to catch a bad selector, a covering overlay, or a
wrong-page navigation. Inspect every final image, and confirm it shows the correct role.

## Capture quality

- Widen the viewport (for example `{ width: 1920, height: 1000 }`) for data-dense screens
  like list views with many columns, so more fits without scroll-and-stitch.
- Dismiss in-scope overlays (onboarding/tour popups, "Getting Started" widgets, cookie
  banners) before the final capture of a screen, so the screenshot documents the actual
  feature, not a widget covering it.
- Save screenshots with a clear ordered naming scheme (`section_NN_description.png`) so they
  drop straight into a document in the right order without manual sorting.
- Optionally embed approved screenshots with [generate-word](../../generate-word/SKILL.md).

## Privacy and cleanup

Review every final image for credentials, tokens, PII and unrelated confidential content.
Prefer approved test data; redact or recapture before sharing, and do not retain unsafe
originals in deliverables. Close browser contexts and delete task-created temporary
credentials, role state files, sensitive persistent profiles and intermediate/debug
captures when no longer needed. Do not delete a user's pre-existing profile or credential
store. Keep only approved final screenshots in the agreed output location.
