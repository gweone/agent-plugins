---
name: sql-migration-scripts
description: Use when writing a SQL script (migration, table/column patch, stored procedure, function, or seed data) for a SharpPS Sitecore solution's database project. Explains how to locate the right project/folder by structure instead of guessing a fixed name, when to use a normal apply-once EF Core migration versus a `*.sql` scripts folder that replays every file on every run, and the idempotency check each statement type needs as a result (table/column existence checks, seed-row existence checks, `CREATE OR ALTER` for procedures/functions).
---

# Adding SQL scripts to the Database project

A SharpPS Sitecore solution has a `database/` solution folder with two projects: one holding the
EF Core `DbContext`, entities, and SQL scripts (called "the Database project" below), and one
holding a console runner that applies them ("the Database.Tools project"). Project names vary per
solution (e.g. `Acme.Database`/`Acme.Database.Tools`) - don't assume a fixed name. Locate them by
structure instead:

1. **Database project** - search the solution for a class deriving from `DbContext` (commonly
   named `ExternalDbContext` or similar) and/or a class deriving from `Migration` under a
   `Migrations/` folder. The project containing those is the Database project.
2. **Scripts folder** - inside that project (typically under `App_Data/Database/...`), find the
   folder of `*.sql` files. Confirm it by checking `appsettings.json` in the sibling
   Database.Tools project for a `MigrationScriptPath` key (or equivalent config value read by a
   `Migration` class) pointing at it - that's the folder replayed on every run (see below). A
   sibling `Manual/`-style folder of `.sql` files that is *not* referenced by that config key holds
   one-off scripts instead, not auto-executed.
3. **Database.Tools project** - the console project referencing the Database project, usually with
   `Program.cs`/`DesignTimeDbContext.cs` and an `OutputType=Exe`.

**If any of these can't be found unambiguously** (no `DbContext` found, multiple candidates, no
`.sql` folder, no `MigrationScriptPath`-equivalent config) - ask the user which project/folder to
use rather than guessing. Silently picking the wrong folder means a script either never runs or
runs somewhere unintended.

There are **two different mechanisms** for changing the schema/data, and picking the wrong one is
the most common mistake:

| Mechanism | Applied | Use for |
|---|---|---|
| EF Core migration (`Add-Migration <Name>` under `Migrations/`) | **Once** - tracked in `__EFMigrationsHistory` like any normal EF migration | Structural changes driven by the C# entity model |
| `.sql` file under the Scripts folder found above | **Every single run** of Database.Tools | Table/column patches, stored procedures, functions, seed data - anything you want re-asserted on every deploy without hand-authoring a new EF migration class each time |

This skill is about the second mechanism. Everything below applies to any SharpPS Sitecore
solution with this project pair - it doesn't depend on a specific solution's name or entities.

## Why "every run" - and why that means idempotent SQL

The Database.Tools project's `Program.cs` does this before applying pending migrations:

```csharp
var context = new DesignTimeDbContext().CreateDbContext(args);
if (await Parse(context, args))   // runs ScriptsMigration.INIT_QUERY
    return;
new MigrationCommandLine<ExternalDbContext>(context).Run(args).GetAwaiter().GetResult();
```

`ScriptsMigration` (in `Migrations/ScriptsMigration.cs`) is a real EF Core `Migration`, but dated
`20000101000000_ScriptsMigration` - the earliest possible timestamp - and `INIT_QUERY` deletes its
own row from `__EFMigrationsHistory` first:

```sql
IF OBJECT_ID(N'__EFMigrationsHistory', N'U') IS NOT NULL
BEGIN
    DELETE FROM __EFMigrationsHistory
    OUTPUT deleted.MigrationId as [Value]
    where MigrationId = '20000101000000_ScriptsMigration'
END
```

Deleting that row before `MigrationCommandLine.Run` executes makes EF Core think
`ScriptsMigration` was never applied, so it reapplies it - **every single time the tool runs**.
`ScriptsMigration.Up()` reads every `*.sql` file under the folder(s) configured by the
`MigrationScriptPath`-equivalent config value (recursively, if a folder), splits each file on `GO`,
and executes the batches via `migrationBuilder.Sql(...)`.

This is deliberate, load-bearing behavior, not a bug to "fix" - it's how the solution re-asserts
stored procedures/functions and patches schema/data without a hand-written EF migration for every
change. The consequence: **every script under the Scripts folder must be safe to run an unlimited
number of times against a database already in the target state.**

A sibling `Manual/`-style folder of `.sql` files, when present, is *not* covered by the
`MigrationScriptPath`-equivalent config - use it for genuinely one-off scripts a DBA runs by hand,
kept in source control for reference but never auto-executed.

## Idempotency rules by statement type

### Creating a table - check existence first

```sql
IF OBJECT_ID(N'dbo.MyTable', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.MyTable
    (
        Id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        Name NVARCHAR(200) NOT NULL
    )
END
GO
```

### Adding a column - check it isn't already there

```sql
IF COL_LENGTH('dbo.MyTable', 'CreatedBy') IS NULL
BEGIN
    ALTER TABLE dbo.MyTable ADD CreatedBy NVARCHAR(200) NULL
END
GO
```

### Dropping a column - check it's still there

```sql
IF COL_LENGTH('dbo.MyTable', 'Obsolete') IS NOT NULL
BEGIN
    ALTER TABLE dbo.MyTable DROP COLUMN Obsolete
END
GO
```

### Seed data - check the row doesn't already exist

```sql
IF NOT EXISTS (SELECT 1 FROM dbo.MyTable WHERE Id = '00000000-0000-0000-0000-000000000001')
BEGIN
    INSERT INTO dbo.MyTable (Id, Name) VALUES ('00000000-0000-0000-0000-000000000001', 'Default')
END
GO
```

Prefer matching on a stable natural/business key (not an identity column) so the check is
meaningful on a database that already has the row from a previous run.

### Stored procedures and functions - `CREATE OR ALTER`, no existence check needed

`CREATE OR ALTER` is itself idempotent, so no `IF OBJECT_ID` guard is needed here - this is the
pattern used by the reference implementation's sample script (`sp.scripts.sql` in its Scripts
folder) and the pattern to copy for any new procedure or function:

```sql
CREATE OR ALTER PROCEDURE SP_SAMPLES
@ID uniqueidentifier,
@CREATE_BY nvarchar(max) = null
AS
BEGIN
    SELECT @ID, @CREATE_BY
END
```

`ScriptsMigration` detects any batch containing ` PROCEDURE ` or ` FUNCTION ` and wraps it in
`EXECUTE('...')` dynamic SQL automatically before running it - this is what lets a
`CREATE OR ALTER PROCEDURE` batch coexist with other statements in the same file without violating
SQL Server's "must be the first/only statement in the batch" rule for procedure/function creation.
You don't need to do this wrapping yourself; just separate batches with `GO` as normal T-SQL.

## Practical checklist for a new script

1. Locate the Database project, Database.Tools project, and Scripts folder as described above -
   ask the user if any of them can't be found unambiguously.
2. Decide: does this need to be re-applied on every deploy (schema/data patch, stored proc,
   function, seed row) -> the Scripts folder. Is it a one-off a DBA runs manually -> a sibling
   `Manual/`-style folder instead (not auto-executed).
3. Name the file descriptively (e.g. `sp.my_procedure.sql`, `patch.mytable.add.createdby.sql`) -
   any `*.sql` under the configured path is picked up, subfolders included.
4. Write every `CREATE TABLE`/`ALTER TABLE ADD|DROP COLUMN`/seed `INSERT` with the matching guard
   above. Use `CREATE OR ALTER` for procedures/functions with no guard.
5. Separate independent statements/batches with `GO` on its own line, matching normal T-SQL
   conventions - the runner splits on `\bGO\b`.
6. Don't include a `USE <database>` statement - the runner comments it out anyway (the connection
   already targets the right database via the configured connection string), so it's dead weight
   at best and misleading at worst.
7. Verify locally by running the Database.Tools console project twice in a row against the same
   database - the second run must be a no-op with no errors. That's the actual acceptance test for
   idempotency, not just eyeballing the guard clauses.
