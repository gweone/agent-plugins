# Version-scoped shipped pipeline catalog

This is a catalog from the documented external source snapshot, **not a newly verified runtime
inventory or a guarantee for the installed version**. Inspect that version's `Pipelines/` and
`Get-Pipeline` output. In particular, `deploy` and `docker` in the authoring examples may exist
in other source versions/workspaces; do not assume they ship with the seven pipelines below.

## Shipped pipelines (all under `Pipelines/`)

| Pipeline | What its processors do |
|---|---|
| `startup` | Bootstraps a session: `Set-TrustPolicy`/Chocolatey profile import, discovers `*.sln`-adjacent projects, generates/invokes EF Core migrations (`New-Migration`, `Invoke-Migration`). |
| `artifact` | Resolves `sharpps.config`/`SolutionPath`, diffs git changes, builds artifact-migration scripts, archives `inetpub`/`database`/`packages`/`documentation` into a deployable artifact. |
| `publish` | Resolves solution + build `Configuration`/`SolutionTargets` (default `Debug`, `restore`+`rebuild`), then publishes selected `Folders` to a target path. |
| `install` | Cross-platform bootstrap: Chocolatey on Windows, native package managers on Linux/macOS, plus a `sharpps-traefik` release-download step. |
| `sif` | Sitecore Install Framework wrapper: prerequisites, cert creation, package downloader, Solr install, CM/CD install (with SXA variants). |
| `sitecore` | Orchestrates a full deploy: publish → DB migration → warm-up (`Start-SiteUp`) → Unicorn sync (`Invoke-SyncUnicorn`). |
| `traefik` | Local reverse-proxy management: resolve `traefik.yml` config, toggle API debug, tail logs, add/edit a dynamic service YAML. |

Prefer reading the installed `00-Help.ps1` and processor source, plus `Get-Pipeline`, for exact
arguments. `Start-Pipeline <name> -Help` requests the usage convention, **not read-only mode**:
predecessors run before `Help` is set and `AlwaysRun` steps may run after abort. Review the full
chain and obtain authorization for any effects before executing even a Help request.

Source trace: `SharpPS.Shells/Pipelines/` in the external source version described above.
See [execution order](registration-and-execution.md) and [module setup](module-setup.md).
Operational deployment/migration/install actions require explicit targets and approval;
`startup` trust/migration behavior is consequential too.
