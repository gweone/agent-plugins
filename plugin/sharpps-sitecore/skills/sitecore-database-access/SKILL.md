---
name: sitecore-database-access
description: Access a SharpPS Sitecore solution's SQL databases over HTTP through DatabaseController's URL pattern (api/SharpPS/Database/{connectionStringName}/{action}) - running raw SQL, listing stored procedures, and calling a stored procedure with parameters. Use for Execute/Procedures/Procedure actions, connectionStringName lookups, self-signed-certificate hosts, or DeriveParameters/ToDictionary failures on this controller.
---

# Database access via DatabaseController

Admin-only HTTP access to a solution's databases through
`DatabaseController`. Not a general SQL or migration skill - for
application-managed, replayed SQL see
[sql-migration-scripts](../sql-migration-scripts/SKILL.md).

## URL pattern

```
https://{hostname}/api/SharpPS/Database/{connectionStringName}/{action}
```

`SharpPS` is the fixed area name - not a parameter, don't ask about it.

- `{hostname}` and `{connectionStringName}` **must be asked of the user**
  before the first call - never infer, guess, or reuse one from an
  earlier example/task.
- `{connectionStringName}` is a named entry under `Settings.GetConnectionString`
  (`App_Config/ConnectionStrings.config` on that host); there is no way
  to enumerate valid names ahead of asking, since listing them requires
  already having a working connection string.
- `{action}` is one of:
  - `Execute(connectionStringName, command)` - raw SQL/DDL/DML via
    `command=`, or an uploaded `.sql` file as the first form file.
  - `Procedures(connectionStringName, page=1, pageSize=20, keyword=null)` -
    paged stored-procedure name list.
  - `Procedure(connectionStringName, procedure)` - derives and binds the
    stored procedure's parameters from same-named form fields and
    executes it; this one reads `Request.Form`, so parameters must be
    **POSTed**, not put on the querystring.

## Certificates

These hosts commonly run a self-signed certificate. From a shell,
bypass the TLS error explicitly (`curl -k`/`--insecure`, PowerShell
`-SkipCertificateCheck`) - only for a host the user has confirmed as
theirs.

From chrome-devtools MCP there is no per-call flag on any of its tools
to bypass a certificate error, and no CLI launch flag is available
either in a typical `--autoConnect` setup (it attaches to the user's
already-running Chrome instead of launching one it controls). Instead,
click through Chrome's own certificate interstitial once, the same way
a person would: `navigate_page`, then if it lands on the "Your
connection is not private" page, `take_snapshot` and `click` through
"Advanced" → "Proceed to {hostname} (unsafe)". Chrome remembers that
exception for the rest of the browser session, so this is only needed
once per host per session, not before every call. See
[Certificate interstitial](references/database-access.md#certificate-interstitial-chrome-devtools-mcp).

## Reaching the host

Prefer sending the request through chrome-devtools MCP instead of
`curl` once the host is reachable (see [Certificates](#certificates)):
open/select a tab on `{hostname}`, then call `evaluate_script` with a
`fetch()` against the endpoint to send data and read the JSON response
back. See
[Chrome MCP recipe](references/database-access.md#chrome-devtools-mcp-recipe).
Fall back to the shell if chrome-devtools MCP isn't available.

## Execution

`Execute` runs arbitrary SQL under the app pool's DB credentials -
treat any call with side effects (`CREATE`/`ALTER`/`INSERT`/`UPDATE`/
`DELETE`/`DROP`) as needing the same authorization a direct database
connection would. Never run it against a host that has not been
explicitly confirmed as the user's own. Clean up any object created for
testing (e.g. a throwaway stored procedure) once verified.

## Verification

An `HTTP 200` from the call is sufficient confirmation that the route,
`connectionStringName`, and (for `Procedure`) parameter binding all work
end-to-end - no need to dig further into the response once the status
is `200`.

## Known bugs to watch for

- `Procedure` can throw *"DeriveParameters requires an open and available
  Connection"* if the connection isn't opened before
  `SqlCommandBuilder.DeriveParameters`.
- Code calling `.ToDictionary()` on the raw `IDataReader`/`.InnerReader`
  from `SharpPSDataApi.CreateReader` can throw *"Invalid attempt to read
  when no data is present"*, or silently return `{"fieldCount": 1}` per
  row instead of real columns, depending on which overload is called.

Fixes are in [Known bugs and fixes](references/database-access.md#known-bugs-and-fixes).

## Related skills

- [sitecore-solution-config](../sitecore-solution-config/SKILL.md) - resolving a local solution's instance URL; does not cover a remote/third-party host.
- [sql-migration-scripts](../sql-migration-scripts/SKILL.md) - the application's own replayed SQL scripts, instead of ad hoc `Execute` calls.
- [sitecore-spe-remoting](../sitecore-spe-remoting/SKILL.md) - connecting to Sitecore itself (items/content), not its SQL databases.
