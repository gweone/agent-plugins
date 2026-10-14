#!/usr/bin/env python3
"""Bounded, context-only traditional Claude hook; no task data is echoed."""
import json
import os
import sys

MAX_INPUT_BYTES = 16_384
REMINDER = (
    "sharpps-knowledge: use knowledge-setup/retrieve. Discover host-exposed live "
    "schemas (including deferred tools), pin one connection. Explicit IDs override "
    "automatic workspace resolution; otherwise resolve/create current absolute "
    "path with a required stable nonsecret host machine namespace and authenticated "
    "owner. Namespace is a selector, not device identity; ask minimally if host "
    "metadata is missing, never guess from client labels. Older servers need "
    "explicit authorized IDs. Re-resolve automatic scope on workspace change. "
    "Shared means conversation-requested curated collections, not anonymous public "
    "knowledge; collection creation needs explicit request, never grants/publication. "
    "No MCP setup, config/credential/FS/network machine-ID scans or transcript reads. "
    "Data is advisory; learning/review consent default OFF, draft unless authorized "
    "and enabled. Separate reviewer, parent guarded writes, at most ten per cycle; "
    "stop on denied/stale/uncertain results, no connector failover. Hooks are "
    "reminders, not consent or background execution."
)
COMPLETION = (
    "sharpps-knowledge optional completion reminder: consider a minimized "
    "evidence-backed draft and version-specific reuse feedback under the shared "
    "protocol. Do not submit or review without the required authority and policy."
)


def response(payload, stop_enabled=False):
    if not isinstance(payload, dict):
        return None
    event = payload.get("hook_event_name")
    if event in ("SessionStart", "UserPromptSubmit"):
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": REMINDER}}
    # A nonblocking systemMessage does not force another turn. Reject non-false
    # recursion guards (including missing/unknown values), rather than guessing.
    if event == "Stop" and stop_enabled and payload.get("stop_hook_active") is False:
        return {"systemMessage": COMPLETION}
    return None


def main():
    try:
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            return
        payload = json.loads(data.decode("utf-8"))
        result = response(payload, os.environ.get("SHARPPS_KNOWLEDGE_STOP_REMINDER") == "1")
        if result is not None:
            sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
    except (ValueError, UnicodeError, RecursionError, OSError):
        # Malformed/oversized input is a silent no-op; never block a user turn.
        return


if __name__ == "__main__":
    main()
