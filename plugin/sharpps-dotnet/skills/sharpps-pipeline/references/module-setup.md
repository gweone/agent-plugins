# Module setup and host selection

Historical external-source guidance, not a freshly verified installation recipe. Confirm the
installed version, repository availability, host, scope, dependencies, and target machine.
**Spec → Plan → Execution:** installation, repository registration/trust, elevation, module import,
and certificate policy changes are distinct choices. Never automatically install a host/module,
trust a repository, or bypass certificate validation. Import runs module initialization code.
The examples below are for review and authorized use, not instructions to execute by default.

## Which PowerShell host to invoke

`SharpPS.Shells` is cross-platform (the `install` pipeline explicitly branches Chocolatey vs.
native Linux/macOS package managers), so don't default to one launcher name without checking:

- **Windows**: both `powershell` (Windows PowerShell 5.1 — built in, legacy) and `pwsh`
  (PowerShell 7+/Core, if installed) may be present. Prefer `pwsh` unless the user explicitly
  asks for Windows PowerShell — it's the actively-maintained line and the same one required on
  Linux/macOS, so defaulting to it keeps behavior consistent across OSes.
- **Linux/macOS**: use `pwsh`; do not assume the Windows `powershell` launcher is available.
  The documented build targets `netstandard2.0`; verify host/dependency compatibility for
  the installed version rather than assuming identical behavior across platforms.

When invoking a cmdlet from a non-PowerShell shell (e.g. this Bash tool, a CI step), call the
host explicitly rather than assuming the ambient shell already is PowerShell:

```bash
pwsh -NoProfile -Command "Start-Pipeline sitecore @{ PublishUrl = 'C:\Custom\Path' } -Verbose"
```

If the user is specifically working inside a Windows PowerShell 5.1 session (not `pwsh`), swap
`pwsh` for `powershell` in the invocation above — verify compatibility with the installed
module/dependencies rather than assuming host parity.

`SharpPS.Shells` is a PowerShell module (`SharpPS.Shells.psd1`/`.psm1`, `netstandard2.0` compiled
cmdlets + shipped `.ps1` scripts) built around one idea: a **pipeline** is a named, ordered list of
scripts (*processors*) that all receive the same shared `[hashtable]$arguments`, so each step can
read what an earlier step decided and write flags later steps react to (most importantly
`Aborted`).

On import, `SharpPS.Shells.psm1`:
1. Loads the compiled `SharpPS.Shells.dll` (see [cmdlet lookup](registration-and-execution.md#the-four-cmdlets)) and dot-sources every
   `Functions/*.ps1` (public helpers, e.g. `Invoke-MSBuild`, `Invoke-SyncUnicorn`) and
   `Privates/*.ps1` (internal helpers).
2. Runs `Register-Pipeline -BasePath Pipelines -Force`, which registers the documented source snapshot's pipeline folders: `artifact`, `install`, `publish`, `sif`, `sitecore`, `startup`, `traefik`.

## Installing the module: the SharpPS gallery, not the public NuGet gallery

`SharpPS.Shells` is published to **`SharpPSGallery`**, a MyGet-backed PowerShell repository —
`https://www.myget.org/F/sharpps/api/v2` — not PSGallery/nuget.org. Register that repository once,
then `Install-Module` from it, exactly as the Sitecore template's bootstrap script does (in that
repo: `SharpPS.VisualStudio.Sitecore.Templates/items/tools/powershell/launcher.ps1`):

```powershell
$Repository    = "SharpPSGallery"
$RepositoryUrl = "https://www.myget.org/F/sharpps/api/v2"

if (-not (Get-PSRepository -Name $Repository -ErrorAction SilentlyContinue)) {
    Register-PSRepository -Name $Repository -SourceLocation $RepositoryUrl -InstallationPolicy Trusted
}

# Idempotency check used by launcher.ps1: only install if Start-Pipeline isn't already available.
if (-not (Get-Command -Name Start-Pipeline -ErrorAction SilentlyContinue)) {
    Install-Module SharpPS.Shells -Repository $Repository -Force -Confirm:$false -Scope AllUsers
}

Import-Module SharpPS.Shells
```

- `-InstallationPolicy Trusted` is the bootstrap's trust choice, not a universal requirement;
  an untrusted repository may prompt. Do not set trust automatically: obtain explicit approval
  or retain interactive confirmation under the user's repository policy.
- `-Scope AllUsers` (as used in `launcher.ps1`) needs an elevated/administrator shell; drop it (or
  use `-Scope CurrentUser`) for a per-user install that doesn't need elevation.
- Gate on `Get-Command Start-Pipeline` (not `Get-Module -ListAvailable`) to check whether the
  module is already usable in the current session before reinstalling — that's the check
  `launcher.ps1` uses.
- If registering against `SharpPSGallery`/MyGet fails on TLS/certificate errors (seen on older
  PowerShell/.NET on some machines), `launcher.ps1` also ships a `Set-CertificatePolicy` helper
  that relaxes `ServicePointManager` TLS/cert validation before registering — do not invoke it automatically, even on failure. Diagnose TLS/certificate trust and repair
  the certificate chain first; relaxing validation requires separate explicit authorization
  and an explanation of the security consequences.
- This is a distinct package/repository from the generic `NugetGallery`-hosted
  `SharpPS.PowerShell.MSBuild` module documented in `SharpPS.Shells/docs/README.md` — don't
  conflate the two; `SharpPS.Shells` (the pipeline module this skill covers) lives on
  `SharpPSGallery`.

## Source traces

- `SharpPS.Shells.psm1`, `SharpPS.Shells.psd1`, `Functions/*.ps1`, `Privates/*.ps1`.
- `SharpPS.VisualStudio.Sitecore.Templates/items/tools/powershell/launcher.ps1` (external bootstrap).
- `SharpPS.Shells/docs/README.md` documents the distinct `SharpPS.PowerShell.MSBuild` package.
- See [registration and execution](registration-and-execution.md) and the [runtime entrypoint](../SKILL.md).
