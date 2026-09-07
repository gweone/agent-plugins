---
name: deploy
description: Deploy built artifacts to the Liferay dev environment. Use when the user asks to deploy, copy jars, copy zips, push to liferay, or deploy a module or client extension.
disable-model-invocation: true
---

Copy built artifacts from the workspace into the Liferay dev deploy folder.

## Deploy HOT Target Path

**Never hardcode this path.** It's environment-specific (differs per machine/docker-compose
setup) and must be confirmed with the user before the first deploy of a session — do not guess
or reuse a path from a different project/skill:

> "Where's the Liferay hot-deploy folder for this environment? (e.g. the
> `.../docker/liferay-dev/mount/deploy/` mount point)"

Store the answer as `DEPLOY_TARGET` and reuse it for the rest of the session — don't ask again
unless the user says it changed.

## Source Paths
- **Modules** (`.jar`): `modules/<module-dir>/build/libs/*.jar`
- **Client Extensions** (`.zip`): `client-extensions/<cx-dir>/dist/*.zip`

## Workflow

This skill always runs in three phases, in order. Never skip straight to Execution —
state the Spec and Plan out loud first so the user can see what's about to be copied where.

### 1. Spec

Determine the concrete target before doing anything:
- Resolve `DEPLOY_TARGET` (ask the user, per above, if not already established this session).
- Which module(s) / client extension(s), or "deploy all"?
- Check the source files actually exist:
  ```bash
  ls modules/<module-dir>/build/libs/*.jar
  ls client-extensions/<cx-dir>/dist/*.zip
  ```
  If nothing found → stop and tell the user to run `/build` first. Do not build automatically.

### 2. Plan

List, by name, exactly which file(s) will be copied to `$DEPLOY_TARGET` before copying
anything — if "deploy all" was requested, enumerate every module/client-extension with output
files found in the Spec step.

### 3. Execution

Copy and confirm each file from the Plan:
```bash
cp modules/<module-dir>/build/libs/<file>.jar \
   "$DEPLOY_TARGET" \
   && echo "✅ <file>.jar copied"

cp client-extensions/<cx-dir>/dist/<file>.zip \
   "$DEPLOY_TARGET" \
   && echo "✅ <file>.zip copied"
```
- If `cp` succeeds → `&& echo` prints ✅
- If `cp` fails → echo is skipped, the shell error is shown instead

## Notes
- Liferay will do Hot deploy automatically, Do not verify file exists in target after copy — Liferay processes and deletes it immediately
- Do not run a build automatically — if artifacts missing, ask user to run `/build` first
