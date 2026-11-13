# Retrieving and analyzing the Jam

Start after clicking **Create** in the Jam submit form (see [extension recording](extension-recording.md)), or when the user asks you to check a Jam. Use whichever retrieval capabilities are actually available.

## 1. Find the Jam

### MCP path

Prefer the most specific route:

1. `searchJams` with `window.from` just before the recording started, newest first; match by title, creation time and author.
2. If it is not available, use the dashboard fallback below.
3. Several candidates: list them and ask the user which one. Never guess.

No result: say no Jam was found. Check Jam's capture state (still `draft` means the form was not submitted); it may also still be uploading or be in another workspace. Retry once after a short wait.

### Dashboard fallback

When search/retrieval MCP tools are unavailable:

1. Ask the user to open [Jam](https://jam.dev/) and select the correct workspace.
2. Ask them to open the Jams/recordings list in the dashboard and locate the new recording by title, creator, or approximate submission time.
3. Ask them to open the Jam, confirm it has finished processing, and copy its share URL into the conversation.
4. If the user can share relevant dashboard evidence (visible timeline, screenshots, console/network details), ask them to paste or provide it. Do not imply that dashboard visibility grants the agent access to data it has not actually retrieved.

If the user provides only a Jam URL and no retrieval tool or supported browser access is available, explain that the agent cannot inspect its private diagnostics in this session. Ask for the relevant evidence from the dashboard or for Jam MCP to be connected.

## 2. Confirm it is ready

With MCP, call `getDetails` and proceed only when the Jam is fully processed. If it is still processing, tell the user and wait or retry only when appropriate; do not analyze partial data as complete.

Without MCP, ask the user to confirm that the dashboard shows the Jam is ready. This is user-reported status, not an agent-verified check; label it accordingly.

## 3. Fetch only what is needed

| Need | MCP tool |
|---|---|
| Title, author, status, link | `getDetails` |
| What happened on screen | `getFrames`, `getScreenshots`, `getVideoChapters` |
| Voice narration | `getVideoTranscript` |
| Console errors | `getConsoleLogs` |
| Failed or slow requests | `getNetworkRequests` |
| User clicks/typing/navigation | `getUserEvents` |
| Combined timeline | `getEvents` |
| Custom metadata | `getMetadata` |

Start with `getDetails` and `getUserEvents`; add logs and network only for errors or failures; frames only when the visual state matters. If a specific tool is unavailable, omit that data and say it was not accessible. Do not substitute assumptions for missing evidence.

## 4. Log availability

If `getConsoleLogs` / `getNetworkRequests` return nothing, say so and give the likely reason (unverified domain, extension limits, or no events recorded). Do not infer "no errors". Without logs, analysis rests on available frames, transcript, and user events and is lower confidence; state that.

For dashboard-only evidence, distinguish what the user reports or shares from what the agent independently inspected. Do not claim structured logs were analyzed unless their contents were actually provided or retrieved.

## 5. Analyze

- Rebuild the user's action sequence that reproduces the problem.
- Correlate console errors and failed requests (status, URL, timing) with the action at that timestamp when those data are available.
- Separate observed facts from suspected cause.
- Redact tokens, cookies, and personal data before quoting.

## Summary template

```text
Jam: <link> (<title>, recorded <time>)
Retrieval: MCP inspected / dashboard evidence supplied by user / URL only
Logs available: console yes/no/unknown, network yes/no/unknown
What the user did: <numbered steps with timestamps, if available>
Evidence: <error/request, timestamp, correlated action>
Likely cause: <statement>, confidence <high/medium/low> and why
Limitations: <missing data or access constraints>
Next step: <fix, more data, or hand-off>
```

## Follow-ups

Only use Jam MCP actions such as comments, feedback, or resource links when the corresponding tools are available and the user has requested or approved the action. Ask before posting comments the user did not request. For deeper flows use Jam's own skills when installed and applicable; do not promise integrations that are not available in the current agent.
