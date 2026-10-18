# Binary attachments on Object Entries

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Binary attachments on Object Entries

A real, confirmed pattern (`liferay-ticket-workspace/client-extensions/liferay-ticket-batch/batch/`):

```
batch/
├── 03-object-entry.batch-engine-data.json
└── attachments/
    ├── TICKET_1/
    │   └── ticket_1.pdf
    ├── TICKET_2/
    └── TICKET_3/
```

In the JSON, reference the file with a placeholder token plus the real filename:

```json
"attachment": {
    "fileBase64": "@batch_object_entry_file_base64@",
    "name": "ticket_1.pdf"
}
```

The build step substitutes `@batch_object_entry_file_base64@` with the actual file's base64
content, matched by the surrounding `attachments/<externalReferenceCode>/` directory convention.
