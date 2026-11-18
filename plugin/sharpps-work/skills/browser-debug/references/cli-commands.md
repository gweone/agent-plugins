# Chrome DevTools CLI commands

Every command below runs through the wrapper: `chrome_cli.sh <command> <arguments>`. This list was generated from the CLI's own help (`chrome-devtools --help`, version 1.13.0). For the exact options of one command run `chrome_cli.sh <command> --help`. How the wrapper works and common recipes: [cli](cli.md).

**Reading the tables.** *Arguments* is the command's usage line: `<x>` is required and positional, `[--x]` is an optional flag. Every command also accepts `--output-format=json`. *Wrapper* says whether the tool exists in a wrapper session: tools that need a start flag the wrapper does not set are `no`. The MCP tool of the same name takes the same arguments as structured fields.

The daemon commands `start`, `status` and `stop` are omitted on purpose: the wrapper manages the daemon (use `chrome_cli.sh --info` and `--sync`).

## Pages and navigation

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `close_page` | `<pageId>` | Closes the page by its index. | yes |
| `handle_dialog` | `<pageId> <action> [--promptText]` | If a browser dialog was opened, use this command to handle it | yes |
| `list_pages` | none | Get a list of pages including extension service workers open in the browser. | yes |
| `navigate_page` | `<pageId> [--type] [--url] [--ignoreCache] [--handleBeforeUnload] [--initScript]` | Go to a URL, or back, forward, or reload. | yes |
| `new_page` | `<url> [--background] [--isolatedContext] [--timeout]` | Open a new tab and load a URL. | yes |
| `resize_page` | `<pageId> <width> <height>` | Resizes the page's window so that the page has specified dimension | yes |
| `select_page` | `<pageId> [--bringToFront]` | Select a page as a context for future tool calls. | yes |

## Input

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `click` | `<pageId> <uid> [--dblClick] [--includeSnapshot]` | Clicks on the provided element | yes |
| `click_at` | `<pageId> <x> <y> [--dblClick] [--includeSnapshot]` | Clicks at the provided coordinates | no (needs --experimentalVision=true) |
| `drag` | `<pageId> <from_uid> <to_uid> [--includeSnapshot]` | Drag an element onto another element | yes |
| `fill` | `<pageId> <uid> <value> [--includeSnapshot]` | Type text into an input, text area or select an option from a `<select>` element. | yes |
| `hover` | `<pageId> <uid> [--includeSnapshot]` | Hover over the provided element | yes |
| `press_key` | `<pageId> <key> [--includeSnapshot]` | Press a key or key combination. | yes |
| `type_text` | `<pageId> <text> [--submitKey]` | Type text using keyboard into a previously focused input | yes |
| `upload_file` | `<pageId> <uid> <filePaths..> [--includeSnapshot]` | Upload a file through a provided element. | yes |

## Inspection and emulation

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `emulate` | `<pageId> [--networkConditions] [--cpuThrottlingRate] [--geolocation] [--userAgent]` | Emulates various features on the target page. | yes |
| `evaluate_script` | `[function] [--pageId] [--sourcePath] [--format] [--args] [--filePath] [--dialogAction]` | Evaluate JavaScript inside the target page or service worker. | yes |
| `get_console_message` | `<pageId> <msgid>` | Gets a console message by its ID. | yes |
| `get_css_styles` | `<pageId> <uid> [--pageSize] [--pageIdx]` | Retrieve matched CSS rules, inline styles (element.style), inherited styles, custom properties, and cascade wrappers (@layer… | yes |
| `list_console_messages` | `<pageId> [--pageSize] [--pageIdx] [--types] [--includePreservedMessages]` | List all console messages for the target page since the last navigation. | yes |
| `take_screenshot` | `<pageId> [--format] [--quality] [--uid] [--fullPage] [--filePath]` | Take a screenshot of the page or element. | yes |
| `take_snapshot` | `<pageId> [--verbose] [--filePath]` | Take a text snapshot of the target page based on the a11y tree. | yes |

## Network

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `get_network_request` | `<pageId> [--reqid] [--requestFilePath] [--responseFilePath]` | Gets a network request by an optional reqid, if omitted returns the currently selected request in the DevTools Network panel. | yes |
| `list_network_requests` | `<pageId> [--pageSize] [--pageIdx] [--resourceTypes] [--includePreservedRequests]` | Lists the most recent requests for the target page since the last navigation. | yes |
| `mock_network` | `<pageId> [--route] [--resourceType] [--body] [--upstream]` | Inspect or update network mocks for a page. | yes |
| `remove_network_mock` | `<pageId> [--route] [--resourceType]` | Remove network mocks matching the supplied stored route and/or resource type. | yes |

## Performance and recording

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `lighthouse_audit` | `<pageId> [--mode] [--device] [--outputDirPath]` | Get Lighthouse scores, failing audits, and the DOM nodes they flag for accessibility, SEO, best practices, and agentic browsing. | yes |
| `performance_analyze_insight` | `<pageId> <insightSetId> <insightName>` | Provides more detailed information on a specific Performance Insight of an insight set that was highlighted in the results of a… | yes |
| `performance_start_trace` | `<pageId> [--reload] [--autoStop] [--ignoreCache] [--filePath]` | Start a performance trace on the target webpage. | yes |
| `performance_stop_trace` | `<pageId> [--filePath]` | Stop the active performance trace recording on the target webpage. | yes |
| `screencast_start` | `<pageId> [--filePath]` | Starts recording a screencast (video) of the target page. | yes |
| `screencast_stop` | `<pageId>` | Stops the active screencast recording on the target page. | yes |
| `set_logpoints` | `<pageId> <logpoints..>` | Set the complete set of logpoints of the selected page: logpoints not in the list are removed, new ones are added, and an empty… | yes |

## Memory

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `analyze_heapsnapshot_contexts` | `<filePath> [--retainedSize] [--scopeInfoNodeId] [--maxNameLength]` | Loads and caches a memory heapsnapshot to identify and rank closure contexts holding dead captured fields—variables no remaining… | yes |
| `close_heapsnapshot` | `<filePath>` | Closes a previously loaded and cached memory heapsnapshot, freeing its memory. | yes |
| `compare_heapsnapshots` | `<baseFilePath> <currentFilePath> [--classIndex] [--maxNameLength] [--pageIdx]` | Loads and caches two memory heapsnapshots and returns the comparison. | yes |
| `get_heapsnapshot_class_nodes` | `<filePath> <id> [--filterName] [--objectId] [--maxNameLength] [--pageIdx]` | Loads and caches a memory heapsnapshot and returns instances of a specific class with their IDs. | yes |
| `get_heapsnapshot_details` | `<filePath> [--filterName] [--objectId] [--maxNameLength] [--pageIdx]` | Loads and caches a memory heapsnapshot and returns all available information including statistics, static data, and aggregated… | yes |
| `get_heapsnapshot_dominators` | `<filePath> <nodeId> [--maxNameLength]` | Loads and caches a memory heapsnapshot and returns the dominator chain for a specific node ID. | yes |
| `get_heapsnapshot_duplicate_strings` | `<filePath> [--pageIdx] [--pageSize] [--maxNameLength]` | Loads and caches a memory heapsnapshot and returns duplicate strings grouped by their value. | yes |
| `get_heapsnapshot_edges` | `<filePath> <nodeId> [--sortBy] [--retainedSize] [--excludePrimitives]` | Loads and caches a memory heapsnapshot and returns outgoing edges (references) for a specific node ID. | yes |
| `get_heapsnapshot_object_details` | `<filePath> <nodeId> [--maxNameLength]` | Loads and caches a memory heapsnapshot and returns detailed information about a specific object by its node ID, including size… | yes |
| `get_heapsnapshot_retainers` | `<filePath> <nodeId> [--maxNameLength] [--pageIdx] [--pageSize]` | Loads and caches a memory heapsnapshot and returns retainers for a specific node ID. | yes |
| `get_heapsnapshot_retaining_paths` | `<filePath> <nodeId> [--maxDepth] [--maxNodes] [--maxSiblings]` | Loads and caches a memory heapsnapshot and returns retaining paths for a specific node ID. | yes |
| `get_heapsnapshot_summary` | `<filePath> [--maxNameLength]` | Loads and caches a memory heapsnapshot and returns snapshot summary stats, including native contexts and their sizes, and… | yes |
| `query_heapsnapshot_objects` | `<filePath> [--className] [--propertyName] [--nodeType] [--retainedSize]` | Loads and caches a memory heapsnapshot and queries objects matching specific filters (className, propertyName, nodeType… | yes |
| `take_heapsnapshot` | `<pageId> <filePath>` | Capture a heap snapshot of the target page. | yes |

## Extensions

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `install_extension` | `<path>` | Installs a Chrome extension from the given path. | yes |
| `list_extensions` | none | Lists the unpacked Chrome extensions loaded in the browser. | yes |
| `reload_extension` | `<id>` | Reloads an unpacked Chrome extension by its ID. | yes |
| `trigger_extension_action` | `<id>` | Triggers the default action of an extension by its ID. | yes |
| `uninstall_extension` | `<id>` | Uninstalls a Chrome extension by its ID. | yes |

## Progressive web apps

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `get_os_app_state` | `<manifestId>` | Returns the OS integration state (badge count and registered file handlers) for an installed web app, identified by its manifest… | no (needs --categoryPwa=true) |
| `install_pwa` | `<manifestId> <installUrlOrBundleUrl> [--displayMode]` | Installs a Progressive Web App (PWA) identified by its manifest ID. | no (needs --categoryPwa=true) |
| `launch_pwa` | `<manifestId> [--url]` | Launches an installed Progressive Web App using its saved display mode. | no (needs --categoryPwa=true) |
| `uninstall_pwa` | `<manifestId>` | Uninstalls a Progressive Web App identified by its manifest ID and closes any open app windows. | no (needs --categoryPwa=true) |

## Other (WebMCP, WebAuthn, third-party tools)

| Command | Arguments | What it does | Wrapper |
|---|---|---|---|
| `configure_webauthn` | `<pageId> <enabled> [--protocol] [--transport] [--hasResidentKey]` | Adds a virtual WebAuthn authenticator to the page. | no (needs --categoryWebauthn=true) |
| `execute_3p_developer_tool` | `<pageId> <toolName> [--params]` | Executes a third-party developer tool exposed by the page. | no (needs --categoryExperimentalThirdParty=true) |
| `execute_webmcp_tool` | `<pageId> <toolName> [--input]` | Executes a WebMCP tool exposed by the page (for debugging tools, use 'execute_3p_developer_tool'). | no (needs --categoryExperimentalWebmcp=true) |
| `list_3p_developer_tools` | `<pageId>` | Lists all third-party developer tools the page exposes for providing runtime information (including debugging WebMCP tools and… | no (needs --categoryExperimentalThirdParty=true) |
| `list_webmcp_tools` | `<pageId>` | Lists all WebMCP tools the page exposes (excluding debugging tools, which are exposed via 'list_3p_developer_tools'). | no (needs --categoryExperimentalWebmcp=true) |

Total: 61 commands (51 available through the wrapper).
