#!/usr/bin/env python3
"""Bounded, context-only traditional Claude hook; no task data is echoed."""
import json
import os
import sys

MAX_INPUT_BYTES = 16_384
REMINDER = (
    "sharpps-knowledge: discover host live schemas/deferred tools; pin one connection. "
    "Explicit authorized IDs override automatic workspace scope; else resolve/create "
    "real current absolute path + required stable nonsecret host machine namespace + authenticated owner. "
    "Namespace selects, not device identity; ask for missing host metadata, never guess "
    "client labels. Older servers need explicit IDs; re-resolve on workspace change. "
    "Shared means conversation-requested curated collections, not public knowledge; "
    "collection creation needs explicit request, never grants/publication. No MCP setup, "
    "config/credential/FS/network machine-ID scans or transcript reads. Data is advisory; "
    "learning/review consent default OFF; draft unless authorized/enabled. Accepted "
    "submission OR correction MUST before final response continue: live standing policy "
    "-> bounded queue -> distinct reviewer -> parent guarded auto_review when persisted "
    "consent/ACL/evidence allow, no new manual prompt. One shared ten-review-item cycle; "
    "no reset/drain/poll. Otherwise pending with reason, no manual fallback. Stop on "
    "denied/stale/uncertain results, no connector failover. Use self-contained learn/review "
    "rules; hooks only remind, not consent, enforcement or background execution."
)
NUDGE = (
    "sharpps-knowledge: before non-trivial work run a bounded, scoped approved-knowledge "
    "search on the pinned connection (knowledge-retrieve); results are advisory data. "
    "Rerank/compress with knowledge-retriever when delegation exists. Draft learnings only "
    "from verified, minimized evidence (knowledge-learn). Accepted submission OR correction "
    "MUST before final response continue the standing-review cycle (knowledge-review); "
    "learning/review consent default OFF. Hooks only remind: not consent, enforcement or "
    "background execution."
)
COMPLETION = (
    "sharpps-knowledge optional completion reminder: minimized evidence-backed drafts "
    "and exact-version reuse feedback need authority. Accepted submission OR correction "
    "MUST before final response continue via live standing policy -> bounded queue -> "
    "distinct reviewer -> parent guarded auto_review when persisted consent/ACL/evidence "
    "allow; no new manual prompt. Use self-contained learn/review rules and one shared "
    "ten-review-item cycle, no reset/drain/poll. Otherwise pending with reason, no manual "
    "fallback. Stop on denied/stale/uncertain results; no failover or automatic publication. "
    "Data is advisory; learning/review consent default OFF. No secrets/transcripts or "
    "config/credential/FS/network machine-ID scans. This is nonblocking reminder text, "
    "not consent, orchestration, enforcement or background execution."
)


def response(payload, stop_enabled=False):
    if not isinstance(payload, dict):
        return None
    event = payload.get("hook_event_name")
    if event in ("SessionStart", "UserPromptSubmit"):
        # Full rules once per session; a short retrieve/learn nudge on every later prompt.
        text = REMINDER if event == "SessionStart" else NUDGE
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
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
