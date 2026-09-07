---
name: liferay-logs
description: Show Liferay Docker container logs. Use when the user asks to check logs, watch logs, see liferay output, tail liferay, or monitor deployment in liferay.
disable-model-invocation: true
---

Stream logs from the Liferay container using Docker Compose.

## Workflow

This skill always runs in three phases, in order. Never skip straight to Execution —
state the Spec and Plan out loud first so the user can see what's about to run.

### 1. Spec

Determine what the user actually wants before running anything:
- A live, following stream, or a one-off snapshot?
- Any specific tail length requested (default: last 100/200 lines)?

### 2. Plan

State the exact command that will run before running it:
- Live stream: `docker compose logs liferay-dev --tail=100 --follow`
- Snapshot only: `docker logs liferay-dev --tail=200`

### 3. Execution

1. For a live stream:
   ```bash
   docker compose logs liferay-dev --tail=100 --follow
   ```

2. For a snapshot (no `--follow`):
   ```bash
   docker logs liferay-dev --tail=200
   ```

3. Watch for key events and summarize what you see:
   - ✅ `Server startup in` → deployment complete
   - 📦 `STARTED` followed by a bundle name → module deployed successfully
   - ❌ `ERROR` or `FAILED` lines → show these prominently so the user can act
   - ⏳ No output yet → tell the user Liferay may still be starting
