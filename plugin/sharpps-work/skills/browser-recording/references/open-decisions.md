# Open decisions and later phases

This skill records only through the Jam Chrome extension driven by Chrome MCP. Chrome access to the user's Chrome (resolved per [resolve-mcp](../../browser-debug/references/resolve-mcp.md)), the Jam extension and a signed-in Jam user are required; Jam MCP is optional for managing the result.

| Question | Default | Change when |
|---|---|---|
| Who starts and stops the recording? | The agent, through Chrome MCP | Jam changes its extension UI or states |
| Who answers the native screen picker? | The user | User asks to launch Chrome with auto-select capture switches |
| Where does the submit form open? | On the user's active tab; locate it via Jam's `iui.html` context | Jam changes its UI host |
| Wait for the user or poll after the picker hand-off? | Wait for the user to say they picked, then verify state | User asks for periodic checks |
| Folder per app? | Move to an existing folder only when the user names it; do not create one unasked | User asks to create one |
| Multiple tabs in one recording? | One target tab per recording | Jam documents multi-tab support |

## Later phases (not implemented)

- Picker automation, only if the user opts in to Chrome auto-select capture switches; never by OS input injection or modifying Jam files.
- Agent workflows: bug diagnosis, reproduction steps, E2E tests (Jam's `jam-to-e2e`), development tickets (`jam-to-ticket`), and proof recordings on pull requests (attach via `addResource`).

Do not promise any of these to the user as available.
