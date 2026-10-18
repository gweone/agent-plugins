# Structured Content: shell succeeds, body remains empty

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

**Update — `StructuredContent` (Web Content) tested live across 4 attempts: shell creation
works, content body population does not (yet) — three targeted fixes, three failures.** Built a
real test file (`className: com.liferay.headless.delivery.dto.v1_0.StructuredContent`,
`"siteId": "L_GUEST"` in parameters **plus** `"siteId": 20126` — the actual numeric group ID —
on the item itself, since `siteId` is a real `type: integer` field on this DTO, not just a batch
parameter) and deployed it four times, fixing one real, evidenced problem each round:

1. **`contentFields: [{"name": "content", "contentFieldValue": {"data": "<p>...</p>"}}]`** — no
   error, task `COMPLETED`, article shell created on Guest (confirmed: real `id`, correct
   `title`/`externalReferenceCode`, Guest's `structured-contents` count went 0→1 — proves Web
   Content batch import against Guest is real, not just theoretical). **But** `contentFields` came
   back `{"data": ""}` — empty. Root-caused by reading `StructuredContentResourceImpl._toFields`:
   the flat `contentFieldValue` path does `Field field = fields.get(entry.getKey()); if (field ==
   null) continue;` against the *new* article's not-yet-populated `Fields`, silently dropping the
   value when the key isn't already present.
2. **Switched to `contentFieldValue_i18n: {"en_US": "<p>...</p>"}`** (a string), reasoning that
   `_containsI18nMap()` being true routes through a different, more thorough
   `DDMFormValuesUtil.toDDMFormValues(...)` path that builds fields from scratch instead of
   looking one up. Result: a real, different, **schema** error this time —
   `Cannot construct instance of ContentFieldValue ... no String-argument constructor` — so
   `contentFieldValue_i18n` is `Map<String, ContentFieldValue>` (an object per locale), not
   `Map<String, String>`.
3. **Fixed to `contentFieldValue_i18n: {"en_US": {"data": "<p>...</p>"}}`** (proper nested
   object). No error, task `COMPLETED`, new article shell created (fresh `id`, since the first
   was deleted). Content **still** empty.
4. **Hypothesized the locale wasn't registering as "available"** for this item (since
   `DDMFormValuesUtil.toDDMFormValues` takes an `availableLocales` set derived from elsewhere,
   and the item used a plain `"title"` string rather than `"title_i18n"`), so switched to
   `"title_i18n": {"en_US": "..."}`. Result: `availableLanguages` on the created article correctly
   showed `["en-US"]` this time (confirming the hypothesis was *partially* right — title-locale
   handling did change), but `contentFields` was **still** empty.

**Stopped here — diminishing returns.** Three real, evidenced fixes in a row, each one changing
observable behavior (a schema error, then a populated `availableLanguages`), yet the content body
never actually saves. This points to something deeper in how `DDMFormValuesUtil.toDDMFormValues`
or the underlying `JournalArticleService` update call handles a *brand-new* article's DDM field
values specifically via this batch path — not a simple shape mistake left to find. If you need
this working, the next real step is reading `DDMFormValuesUtil.toDDMFormValues` itself line by
line (not guessing at more JSON shapes), or testing whether **`UPDATE`-ing an already-existing**
article (created some other way first, so its `Fields` aren't empty) succeeds where `CREATE`
doesn't — that would confirm/deny the `_toFields` `fields.get(key) == null` theory precisely.
