---
name: build
description: Build the project using Gradle. Use when the user asks to build, compile, run gradlew, or run a clean build.
disable-model-invocation: true
---

Run a full Gradle clean build from the workspace root.

## Workflow

This skill always runs in three phases, in order. Never skip straight to Execution —
state the Spec and Plan out loud first so the user can see what's about to run.

### 1. Spec

Determine the concrete target before doing anything:
- Whole workspace build, or a specific module (e.g. "build only my-module")?
- Confirm the current directory is the workspace root (where `gradlew` exists) — `cd` there first if not.

### 2. Plan

State the exact command that will run before running it:
- Whole workspace: `./gradlew clean build`
- Single module: `./gradlew --project-dir modules/<module> clean build` (or `:my-module:clean :my-module:build`)

### 3. Execution

1. Run the command from the Plan.
2. Wait for the build to complete.
3. Report the result:
   - If **SUCCESS** → tell the user the build passed and list any `.jar` or `.zip` output files found under:
     - `modules/*/build/libs/*.jar`
     - `client-extensions/*/dist/*.zip`
   - If **FAILED** → show the first error block from the output (the `> Task :...` failure lines) so the user can act on it immediately.

## Notes
- Do not skip `clean` — always run `clean build` together to avoid stale output.
- Do not deploy after building unless the user explicitly asks.
