# Deployment and lifecycle

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

**Deployment, redeployment, OSGi mutation, and container restart require explicit user authorization.** Bundle activation immediately writes live data; preparing files is not permission to deploy.

## Deploying / re-running

- Client Extension form: build with `./gradlew :client-extensions:<name>:clean
  :client-extensions:<name>:build` (find the exact Gradle project path with `./gradlew projects`
  — it's `:client-extensions:<dir-name>`, not the bare directory name). `blade gw deploy`/`gradlew
  clean deploy -Ddeploy.docker.container.id=$(docker ps -lq)` is Liferay's documented one-shot
  build+deploy command; manually `cp dist/<name>.zip` into the deploy mount works identically and
  is what was used throughout this skill's testing.
- A Site Initializer runs the instant its bundle activates (see [packaging](packaging-and-targeting.md)) — there's no
  separate "pick an initializer" step for the CX form once `siteExternalReferenceCode` is set.
  Re-running (redeploy against the same already-initialized site) is generally idempotent
  **except** where noted in [limitations](limitations.md) (`DuplicateObjectRelationshipException`,
  `DuplicateFolderNameException` from ERC mismatches).
- **Verifying a run actually happened — INFO-level logs, not just "no errors":**
  ```bash
  docker logs --since 2m <container> 2>&1 | grep -E "BundleSiteInitializer|ERROR|Exception"
  ```
  A real run prints `Initializing <key> for group <id>`, one `Invoking <step> took <n> ms` line
  per resource type in dependency order, then `Initialized <key> for group <id> in <n> ms`. A
  step that throws aborts the *entire* `initialize()` call (wrapped in `InitializationException`)
  — nothing after the failing step runs, so don't assume partial success. If you see **only**
  `"Processing <name>.zip"` from `AutoDeployScanner` and nothing else, the OSGi bundle install
  itself stalled (see the "stuck deploy" entry in [deployment lifecycle](deployment-and-lifecycle.md)) — that is not a successful run, even
  though it looks harmless.
- Bounded `docker logs` calls only — `docker logs <container>` with no `--since`/`--tail` can
  hang scanning full history on a long-lived dev container. Always use `--since <Ntime>` or
  `--tail <N>`.
- The OSGi gogo shell is the fastest way to check bundle state directly:
  `docker exec <container> bash -c "(printf 'lb <name>\r\n'; sleep 2; printf 'disconnect\r\n';
  sleep 1) | telnet localhost 11311"` — look for `Active` (or `Resolved`, which is also normal for
  a resource-only bundle with no Activator/DS components; don't read "not Active" as failure by
  itself).

## Stuck redeploy after manual uninstall

**A manually `uninstall`-ed CX bundle can get permanently stuck on redeploy** — if you uninstall
a site-initializer bundle via the OSGi console (e.g. to force a fresh `addingBundle()` re-trigger
for testing), redeploying the *same* zip afterward can silently no-op forever: `AutoDeployScanner`
logs `"Processing <name>.zip"` but the bundle never reappears, even across multiple rebuilds with
different checksums. A `stop`/`start` cycle on an already-installed bundle does **not** re-fire
`addingBundle()` either (only a genuine fresh install does, and the deploy scanner's own tracking
gets confused once you've manually torn down its bundle). **Fix: restart the whole container**
(`docker restart <container>`) — this forces a clean OSGi rescan on boot and reliably recovers.
Avoid manually uninstalling a CX bundle via the OSGi console at all if you can help it; prefer
redeploying a content-different zip and waiting for the directory watcher's natural
stop/start-on-update cycle, which *does* work.
