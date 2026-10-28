# Debugging playbook

Tool names are from chrome-devtools-mcp; check the live tool list, since names and
availability depend on server version and flags.

## Start every investigation the same way

1. `list_pages`, then `new_page` or `select_page`.
2. `navigate_page` to the URL, then `wait_for` text you expect.
3. `take_snapshot` to get `uid`s and confirm you are on the intended screen and role.
4. Reproduce the symptom with `click`, `fill`, `press_key`. Re-snapshot between steps.

## Symptom → tools

| Symptom | Tools |
|---|---|
| Blank/broken UI, JS error | `list_console_messages` (filter by `types`), `get_console_message` for the stack, then `evaluate_script` for runtime state |
| Request fails, wrong data, 4xx/5xx | `list_network_requests`, then `get_network_request` by `reqid` for headers, status, and body |
| Layout or style wrong | `get_css_styles` on the element `uid` for the matched rules, cascade, and CSS variables; `evaluate_script` for computed values |
| Responsive or device bug | `resize_page` or `emulate` (viewport, device, network and CPU throttling, geolocation, color scheme) |
| Slow page | `performance_start_trace`, reproduce or reload, `performance_stop_trace`, then `performance_analyze_insight` on the named insights (LCP, layout shift, render-blocking, and so on) |
| General quality | `lighthouse_audit` (accessibility, SEO, best practices; it is not a performance trace) |
| Memory growth | start with `--memoryDebugging`, then `take_heapsnapshot`, repeat the action, and `compare_heapsnapshots` |
| Dialog blocks the flow | `handle_dialog` |
| Need the user to look | `take_screenshot`, or `open_devtools`/`reveal_in_devtools` if available |

## Method

- **Isolate**: change one thing per run (fresh page, cache off via `emulate`/reload,
  different viewport). Note what flipped the result.
- **Network first for "wrong data"**: the UI may be faithfully rendering a bad response.
  Check the request/response pair before suspecting the frontend.
- **Console order matters**: the first error is usually the cause; later ones cascade.
- **Traces**: record the shortest scenario that shows the problem. Lab traces on a dev
  machine differ from field data; say which one a number comes from.
- **Cookie/session bugs**: inspect cookie attributes (`Secure`, `SameSite`, domain,
  path, expiry) and the `Set-Cookie`/`Cookie` headers via `get_network_request`.
  Report names and attributes only, never values.
- **Local virtual hosts**: if the real hostname doesn't resolve here, the browser
  needs a resolver rule (see the `screen-capture` skill's routing notes) or the server
  started with matching Chrome args; Host-header tricks are unreliable.

## Output hygiene

- Save big captures (traces, heap snapshots, full snapshots) with `filePath` into the
  scratch/agreed folder, then summarize; don't paste them.
- Redact tokens, cookies, auth headers, and personal data before quoting.

## Hand-off to QA

Once the cause is fixed, convert the repro into a regression check with
[browser-qa](../../browser-qa/SKILL.md) so the bug stays fixed.
