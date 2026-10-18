---
name: screen-capture
description: Capture real web-app screenshots with Playwright/Chromium for documentation, manuals, or visual login/setup/error flows. Use for authenticated role-specific captures, reusable storageState, local virtual-host routing with --host-resolver-rules, selector debugging, and screenshot verification; not mockups.
---

# Screen capture via headless browser

Capture the real running app, not a mockup. Playwright capture logic works across
Windows, macOS, and Linux; dependency setup and credential-file encoding need care.

## Workflow: Spec → Plan → Capture → Review

1. **Spec** — identify screens/flows, user roles, target URL/port, local/container
   routing, and final output location. Ask when “document the whole app” is ambiguous.
2. **Plan** — state approved logins and credential sources, navigation per image,
   and intended UI actions before running anything. A restricted view may need a
   different account from an admin view.
3. **Prepare** — inspect the existing environment first; installation requires
   authorization. Follow [setup and local routing](references/setup-and-local-routing.md)
   for Playwright, a smoke test, and local-domain `--host-resolver-rules`.
4. **Capture** — use an isolated context and separate role state files. Follow
   [authentication and capture](references/authentication-and-capture.md) for login,
   credential handling, selectors, rendering waits, and iterative debugging.
5. **Review** — read back every screenshot after meaningful steps and inspect every
   final image. Exit status 0 is not proof of the intended screen or correct role.
6. **Finish** — retain approved images in the agreed location; close contexts and
   clean up sensitive session artifacts and unsafe intermediate captures.

## Boundaries and capture quality

- Installation, credential retrieval, and UI interactions must stay within explicit
  user-approved scope. Ask before unapproved writes, destructive actions, or effects
  outside the capture task; do not silently modify hosts files or system settings.
- Never print secrets or embed them in scripts/transcripts. Credential files,
  storageState, and persistent profiles are sensitive, not deliverables.
- For local virtual hosting, navigate using the real hostname with a Chromium
  resolver rule. Host-header route interception is unreliable, not the workaround.
- Scope selectors to the intended visible container. Strict locator actions may
  throw on multiple matches; choosing `.first()` can instead hide an ambiguity.
- Use a wide viewport for dense screens, dismiss in-scope overlays, and name images
  in order, e.g. `section_NN_description.png`. Check for PII and confidential data.

## Detailed guidance and composition

- [Setup and local-domain routing](references/setup-and-local-routing.md): install
  commands, Linux dependencies, smoke test, resolver example, hosts-file diagnosis.
- [Authentication and capture](references/authentication-and-capture.md): role state,
  credential redirection/encoding, selector pitfalls, error flows, visual reread, cleanup.
- Optionally embed approved screenshots with [generate-word](../generate-word/SKILL.md).
