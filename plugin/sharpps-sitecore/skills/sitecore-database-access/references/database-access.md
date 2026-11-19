# Database access reference

## Known bugs and fixes

### `Procedure`: connection never opened before `DeriveParameters`

```
System.InvalidOperationException: DeriveParameters requires an open and
available Connection. The connection's current state is closed.
   at System.Data.SqlClient.SqlCommandBuilder.DeriveParameters(SqlCommand command)
   at SharpPS.Sitecore.Development.Controllers.DatabaseController.Procedure(...)
```

`SqlCommandBuilder.DeriveParameters` requires an **open** connection, but
the controller only calls `con.CreateCommand()`, never `con.Open()`:

```csharp
// before (throws)
using (var con = new SqlConnection(connectionString))
using (var cmd = con.CreateCommand())
{
    cmd.CommandText = procedure;
    cmd.CommandType = CommandType.StoredProcedure;
    SqlCommandBuilder.DeriveParameters(cmd); // connection is still closed here
    ...
}

// fixed
using (var con = new SqlConnection(connectionString))
using (var cmd = con.CreateCommand())
{
    con.Open();
    cmd.CommandText = procedure;
    cmd.CommandType = CommandType.StoredProcedure;
    SqlCommandBuilder.DeriveParameters(cmd);
    ...
}
```

### `Procedures`/raw reader: wrong `ToDictionary` overload

`SharpPSDataApi.CreateReader(...)` returns a reader wrapper exposing
`.InnerReader` (the real `IDataReader`). There are (at least) two
`ToDictionary` extensions in play, and calling the wrong one on the wrong
object either throws or silently returns garbage:

- Calling `.ToDictionary()` on the **wrapper itself** (not `.InnerReader`)
  reflects the wrapper's own properties instead of the result set, so
  every row comes back as `{"fieldCount": 1}` with no real columns - a
  silent-shape bug, not an exception.
- Calling `.ToDictionary()` directly on `.InnerReader` (the raw
  `IDataReader`) can throw:
  ```
  System.InvalidOperationException: Invalid attempt to read when no data is present.
     at System.Data.SharpDataReaderExtensions.ToDictionary(IDataReader reader)
     at SharpPS.Sitecore.Development.Controllers.DatabaseController.Procedures(...)
  ```

The safe pattern - already used by `Execute` - is to load the reader into
a `DataTable` first, then call `ToDictionary()` on the `DataTable`:

```csharp
// before (either silently wrong, or throws, depending on which call site)
return Api(result.ToDictionary());             // wrapper reflection bug
return Api(result.InnerReader.ToDictionary());  // reader-state bug

// fixed - matches Execute's existing working pattern
DataTable table = new DataTable();
table.Load(result.InnerReader);
return Api(table.ToDictionary());
```

`Execute` itself is already correct because it does exactly this for
every result set:

```csharp
var reader = api.CreateReader(command);
List<DataTable> results = new List<DataTable>();
do
{
    DataTable table = new DataTable();
    table.Load(reader.InnerReader);
    results.Add(table);
} while (!reader.InnerReader.IsClosed);
return Api(results.Select(x => x.ToDictionary()));
```

Use this `DataTable.Load` + `DataTable.ToDictionary()` pattern for any
new code built on `SharpPSDataApi.CreateReader`.

## curl recipe

Use only against a host the user has confirmed as theirs; `-k` skips
certificate verification for a self-signed cert.

```bash
HOST="https://{hostname}"          # ask the user - never assume or reuse
CS="{connectionStringName}"        # ask the user - never assume or reuse
# the area segment is always the literal "SharpPS" - not a variable

# Procedures: list, paged and keyword-filtered - GET/querystring
curl -sk -G "$HOST/api/SharpPS/Database/$CS/Procedures" \
  --data-urlencode "keyword=SOME_PREFIX" \
  --data-urlencode "pageSize=20"

# Execute: raw SQL
curl -sk -G "$HOST/api/SharpPS/Database/$CS/Execute" \
  --data-urlencode "command=CREATE PROCEDURE SP_SAMPLE_DATABASE @p1 INT, @p2 INT AS BEGIN SELECT @p1 AS P1, @p2 AS P2 END"

# Procedure: call it - parameters MUST be POSTed (Request.Form), not querystring
curl -sk "$HOST/api/SharpPS/Database/$CS/Procedure?procedure=SP_SAMPLE_DATABASE" \
  --data-urlencode "p1=111" --data-urlencode "p2=222"

# Clean up the throwaway procedure once verified
curl -sk -G "$HOST/api/SharpPS/Database/$CS/Execute" \
  --data-urlencode "command=DROP PROCEDURE SP_SAMPLE_DATABASE"
```

## Certificate interstitial (chrome-devtools MCP)

None of the chrome-devtools MCP tools expose a flag to bypass a
certificate error, and no CLI launch flag helps either in a typical
`--autoConnect` setup, since that attaches to the user's own
already-running Chrome instead of letting the server launch (and
configure) its own - `--acceptInsecureCerts` and
`--chromeArg='--ignore-certificate-errors'` only take effect when
chrome-devtools-mcp itself launches Chrome.

Instead, click through Chrome's own interstitial once per host, the
same way a person would. It is a normal HTML page, not a native
dialog, so `take_snapshot` + `click` reach it:

```
mcp__chrome-devtools__new_page(url: "https://{hostname}/")
# or mcp__chrome-devtools__list_pages / select_page to reuse an existing tab

mcp__chrome-devtools__take_snapshot(pageId: <id from new_page/list_pages>)
# If the snapshot shows "Your connection is not private" / "Privacy
# error" instead of the real site, it's the certificate interstitial.
```

If it's the interstitial, click through it (uids come from the
snapshot just taken):

```
mcp__chrome-devtools__click(pageId: <id>, uid: <uid of the "Advanced" element>)
mcp__chrome-devtools__take_snapshot(pageId: <id>)
# the snapshot now includes a "Proceed to {hostname} (unsafe)" link
mcp__chrome-devtools__click(pageId: <id>, uid: <uid of that link>)
```

This lands on the real page, and Chrome remembers the exception for
that host/certificate for the rest of the browser session - only do
this once per host per session, not before every subsequent call.

Once past the interstitial (or if it never appeared), send the actual
request from inside that page with `evaluate_script`.
`{connectionStringName}` below is never a literal - it is whatever
value the user gave when asked:

```
mcp__chrome-devtools__evaluate_script(
  pageId: <same id>,
  function: `async () => {
    const res = await fetch(
      "/api/SharpPS/Database/{connectionStringName}/Procedure?procedure=SP_SAMPLE_DATABASE",
      { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "p1=111&p2=222" }
    );
    return { status: res.status, body: await res.text() };
  }`
)
```

Use a relative path (as above) when the tab is already open on the
target host, so `fetch` stays same-origin; use the full `https://...`
URL instead if calling cross-origin from a different open tab. For
`Procedures`/`Execute` (GET/querystring), build the URL with the query
string and omit `method`/`body`/`headers`.

## Verification

A `200` status from the response above is enough to confirm the route,
`connectionStringName`, and (for `Procedure`) parameter binding all
work. No need to inspect the payload further once the status is `200`.

## Safety boundary

- `Execute` is unrestricted raw SQL under the app pool's DB credentials -
  functionally equivalent to a SQL admin console exposed over HTTP.
- Never call any of these three actions against a host that has not been
  explicitly confirmed as the user's own (sandbox/staging/dev) - a
  domain that looks like it belongs to a third party or a production
  system is not something to probe on the strength of "ignore SSL" or a
  connection-string name alone.
- Prefer the narrowest action for the job: `Procedures` to enumerate,
  `Procedure` to call something that already exists, and reserve
  `Execute` for genuinely ad hoc SQL (including the throwaway
  create/drop needed to verify `Procedure`'s parameter binding).
