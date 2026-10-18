# Batch deployment, deduplication, and verification

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

**Obtain explicit user authorization before deploying or redeploying.** Activation immediately executes live imports, including against system sites. File preparation alone is not deployment permission.

## Deploying — same OSGi auto-trigger pattern as Site Initializer, same LXC red herring

Confirmed by reading `BatchEngineBundleTracker`
(`modules/apps/batch-engine/batch-engine-service/.../internal/bundle/BatchEngineBundleTracker.java`):
a `BundleTrackerCustomizer` tracking `Bundle.ACTIVE` that checks for the
`Liferay-Client-Extension-Batch` manifest header (set by `CreateClientExtensionConfigTask` when
`type: batch`) and, if present, automatically reads every `*.batch-engine-data.json` in the bundle
via `BatchEngineUnitReader` and runs them through `BatchEngineUnitProcessor` — **fully automatic
on bundle activation**, identical in spirit to `SiteInitializerClientExtension`'s `addingBundle()`.

- **Building it also generates a `Dockerfile`/`LCP.json`** (confirmed by reading
  `CreateClientExtensionConfigTask` directly — `batchType` is set to `"batch"` and both files are
  written unconditionally). **This is still an LXC-only artifact, irrelevant for self-hosted
  Docker** — same conclusion as the Site Initializer skill's [initializer packaging](../../liferay-site-initializer/references/packaging-and-targeting.md), for the same reason: the
  manifest header is what the in-process `BatchEngineBundleTracker` actually keys off, not
  anything in those generated files. Don't be misled into thinking a separate `liferay/batch`
  container run is required on a plain `liferay/dxp` container — it isn't, the bundle tracker
  handles it the instant the bundle activates.
- **Re-deploy dedup is per-bundle-`lastModified`, not per-content-hash**: `BatchEngineUnitProcessorImpl._isProcessed()`
  writes a marker file (`bundle.getDataFile(...)`) keyed by the bundle's `lastModified` timestamp.
  Redeploying byte-identical content with a genuinely new build (new `lastModified`) reprocesses;
  redeploying without rebuilding does not. This mirrors the Site Initializer skill's
  AutoDeployScanner dedup caveat — always do a fresh `clean` + `build` before redeploying to test
  a fix, not just `cp` the same already-built zip again.
- Verify a run happened via the same `docker logs --since <Ntime> | grep -E "BatchEngine|ERROR|Exception"`
  approach as the other skill. **The log lines that actually appeared in a real successful run**
  were `BatchEngineImportTaskExecutorImpl:106 Started batch engine import task <id>` and
  `BatchEngineImportTaskExecutorImpl:195 Finished batch engine import task <id> in <n>ms` — one
  pair per `*.batch-engine-data.json` file, in filename order. (`BatchEngineUnitProcessorImpl`'s
  own `"Successfully enqueued/deployed batch file..."` INFO lines exist in source but did not
  appear in practice — don't rely on those specifically; `BatchEngineImportTaskExecutorImpl`'s
  lines are the ones actually observed.) **Total silence (bundle goes `Active`, zero log lines at
  all, not even the AutoDeployScanner's "Processing..." follow-up) is the single biggest red
  flag** — it means `addingBundle()` returned at its very first check, almost always because the
  `Liferay-Client-Extension-Batch` header is missing. Check immediately with:
  ```bash
  unzip -l dist/<name>.zip | grep batch/          # is the batch/ folder even in the artifact?
  # then, after deploying:
  docker exec <container> bash -c "(printf 'headers <bundleId>\r\n'; sleep 2; printf 'disconnect\r\n'; sleep 1) | telnet localhost 11311" | grep Liferay-Client-Extension-Batch
  ```
  Missing from either → you're hitting the missing `assemble:` block from [mandatory assemble block](packaging.md), not a data
  or filter-matching problem. **Always verify this before debugging anything else** — it was the
  actual root cause the one time this was reproduced, and every plausible-looking alternative
  theory (OSGi service filter mismatches, `taskItemDelegateName` typos, dedup-by-`lastModified`)
  was a dead end until this was checked.
- **Don't trust the data until you check it directly** — a clean Active bundle with zero errors
  is not proof of success (see above). The only conclusive check is querying the actual resource
  afterward and confirming `dateModified` moved to the deploy time.
