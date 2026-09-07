---
name: clean-logs
description: Clear Docker container logs. Use when user asks to clean logs, clear logs, flush logs, or reset logs for any docker container.
disable-model-invocation: true
---

Truncate a Docker container's logs to zero.

## Workflow

This skill always runs in three phases, in order. Never skip straight to Execution —
state the Spec and Plan out loud first so the user can see which container's logs are about to
be wiped.

### 1. Spec

Determine the concrete target container before doing anything:
- If `$ARGUMENTS` is given, that's the container name/id.
- If no argument, list running containers and ask the user which one:
  ```bash
  docker ps --format "table {{.Names}}\t{{.Status}}"
  ```
  Wait for the user to specify before continuing.

### 2. Plan

State the exact command that will run, naming the resolved container, before running it:
```bash
truncate -s 0 $(docker inspect --format='{{.LogPath}}' <container>)
```

### 3. Execution

```bash
truncate -s 0 $(docker inspect --format='{{.LogPath}}' <container>) && echo "✅ <container> logs cleared"
```

## Notes
- Does not restart the container — safe to run while container is live
- Requires sudo if permission denied:
  `sudo truncate -s 0 $(docker inspect --format='{{.LogPath}}' <container>)`
