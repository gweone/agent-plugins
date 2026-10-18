---
name: sql-migration-scripts
description: Write replay-safe SQL table/column patches, stored procedures, functions, or seed data for a SharpPS Sitecore Database.Tools runner. Locate MigrationScriptPath, choose apply-once EF Core migrations versus replayed SQL or manual scripts, and check idempotency guards and GO batches.
---

# Database SQL scripts

Use for the solution's application Database/Database.Tools project pair,
located by structure rather than a fixed project name. The configured SQL
scripts replay **every run**; ordinary EF Core migrations apply once.

## Checklist

1. Locate the `DbContext`/`Migrations` project and its referencing console
   runner. Confirm the scripts path from the runner's `MigrationScriptPath`
   or equivalent setting; ask if any project or folder is ambiguous.
2. Choose the mechanism: entity-model structure changes use an EF Core
   migration; replayed patches/procedures/functions/seeds use configured SQL;
   genuinely manual one-offs belong outside the configured replay path.
3. Name the `.sql` descriptively. All matching files under the configured path,
   including subfolders, are picked up.
4. Guard table creation, column addition/removal, and seed insertion; use
   `CREATE OR ALTER` for procedures/functions. Every replay must remain safe.
5. Put `GO` on its own line between batches. Omit `USE <database>`; the
   connection selects the database and the runner comments `USE` out anyway.
6. Verify locally by running Database.Tools twice against the same database;
   the second run must be a no-op with no errors, not merely look guarded.

## Focused lookup

- [Locate the projects, configured scripts path, and manual folder](references/sql-script-migrations.md#adding-sql-scripts-to-the-database-project)
- [Why ScriptsMigration resets its own history and replays every run](references/sql-script-migrations.md#why-every-run---and-why-that-means-idempotent-sql)
- [Statement-specific guards and examples](references/sql-script-migrations.md#idempotency-rules-by-statement-type)
- [CREATE OR ALTER and automatic dynamic-SQL wrapping](references/sql-script-migrations.md#stored-procedures-and-functions---create-or-alter-no-existence-check-needed)
- [File naming, GO splitting, USE handling, and two-run acceptance test](references/sql-script-migrations.md#practical-checklist-for-a-new-script)

## Constraints to retain

- Do not "fix" the deliberate removal of ScriptsMigration's history row.
- Do not guess a script folder: the wrong path can skip execution or run SQL
  somewhere unintended. A sibling `Manual/` folder is not automatically replayed.
- Match seeds on a stable natural/business key rather than an identity value.
- The runner wraps procedure/function batches in `EXECUTE('...')` itself;
  do not add that wrapper manually. Its batch splitter uses `\bGO\b`.

## Related skills

- [sitecore-solution-config](../sitecore-solution-config/SKILL.md) — solution-root configuration, not the runner's replay rules.
- [sitecore-template-items](../sitecore-template-items/SKILL.md) — Sitecore template/item work rather than application-database SQL.
