# Sitecore connection recipes

Resolve URL and credentials with [solution configuration](../../sitecore-solution-config/SKILL.md) first. Live writes need user authorization; a denied tool call is a stop, not a reason to switch tools.

## Running this from Claude Code specifically

Claude Code's auto mode classifier treats `New-SPESession`/
`Invoke-RemoteScript` calls that create or modify items on a real instance
as a high-risk write action and blocks them by default - confirmed live on
both the PowerShell tool and the Bash tool (invoking `powershell.exe`
directly), independent of which one is tried. A pure read/connectivity
check (e.g. one `Get-Item` inside `Invoke-RemoteScript`) was not blocked
the same way; the block is specifically about live writes to a remote or
shared instance, consistent with how the harness treats any other
consequential write to shared infrastructure.

Getting past this for a session that genuinely needs to create items live
requires an explicit project permission entry, and that's a decision for
the user to make and ask for - don't add it on your own initiative before
they've said they want live SPE execution to proceed. If they do ask,
project settings documentation covers where such an entry belongs; a
project-local, gitignored settings file (not the shared/committed one) is
the appropriate place for something this specific to one developer's
instance and default credentials. After it's added, a fresh settings load
may be needed before the harness honors it - if the very next attempt is
still blocked, that's the likely reason, not a sign the entry is wrong.

## Bootstrap the PowerShell module first

Before running any Sitecore-instance operation, bootstrap the `SharpPS.Shells`
PowerShell module via the solution's `tools/powershell/launcher.ps1`. This
script is what installs/imports the module - don't `Import-Module
SharpPS.Shells` directly without it, since it also registers the PSRepository
the module is published to and trusts the self-signed certs typically needed
to reach a local Sitecore instance over HTTPS.

```powershell
# from the solution root, elevated PowerShell
.\tools\powershell\launcher.ps1
```

What it does:
- Registers the `SharpPSGallery` PSRepository (`https://www.myget.org/F/sharpps/api/v2`) if not already registered
- Trusts self-signed certs (`Set-CertificatePolicy`) so `Invoke-WebRequest`/`Invoke-RestMethod` can reach local HTTPS Sitecore instances
- Installs `SharpPS.Shells` from that repository if `Start-Pipeline` isn't already available on the machine, then `Import-Module SharpPS.Shells`
- Runs the `Install` pipeline for `git`, the Chocolatey Visual Studio extension package, and `dotnet-sdk`

**Without admin rights, don't run `launcher.ps1` as-is** - its
`Install-Module SharpPS.Shells ... -Scope AllUsers` line hard-fails
(`AdminPrivilegeRequiredForAllUsersScope`) on a non-elevated shell, live-
confirmed. Replicate its steps manually with `-Scope CurrentUser` instead of
running the script verbatim:

```powershell
$Repository = "SharpPSGallery"
if (-not (Get-PSRepository -Name $Repository -ErrorAction SilentlyContinue)) {
    Register-PSRepository -Name $Repository -SourceLocation "https://www.myget.org/F/sharpps/api/v2" -InstallationPolicy Trusted
}
[Net.ServicePointManager]::SecurityProtocol = "Tls, Tls11, Tls12, Ssl3"
Install-Module SharpPS.Shells -Repository $Repository -Force -Confirm:$false -Scope CurrentUser
Import-Module SharpPS.Shells
```

**`New-SPESession` also needs the separate `SPE` module** (Sitecore
PowerShell Extensions' own Remoting *client* module, `New-ScriptSession`'s
home) - `SharpPS.Shells` calls into it but does not install it, so a fresh
machine needs it pulled from PSGallery too (`SPE`, not `SharpPS.Shells` -
confirmed live as two separate packages):

```powershell
Install-Module SPE -Repository PSGallery -Force -Confirm:$false -Scope CurrentUser -AllowClobber
Import-Module SPE
```

Without this, `New-SPESession` fails with `Import-Module : The specified
module 'SPE' was not loaded` and `New-ScriptSession` not recognized - easy
to misread as an SPE Remoting *server*-side problem when it's actually a
missing *client*-side module.

## Logging into a Sitecore instance

Any authenticated interaction with the instance (publish, admin pages, etc.)
goes through `New-SitecoreSession` first - it's the cmdlet the module uses
under the hood to authenticate. It logs into `$Url/sitecore/login`, scrapes
the login form (`Get-HtmlInputs`), submits the credentials, and returns a
`WebRequestSession` object to reuse in subsequent `Invoke-WebRequest` calls
via `-WebSession`.

```powershell
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$webSession = New-SitecoreSession -Url $Url -Username $Username -Password $securePassword

Invoke-WebRequest -Uri "$Url/sitecore/admin/dbbrowser.aspx" -WebSession $webSession -Method Post -Body @{ ... }
```

- `-Url` - Sitecore instance base URL, e.g. `https://mysite.dev.local`
- `-Username` / `-Password` (`SecureString`) - Sitecore admin credentials; functions built on top of this (`Invoke-SitecorePublish`, `Get-UnicornAutoPublish`) default `Username` to `admin` and `Password` to `b` when not overridden
- Calls `Set-TrustPolicy` internally, so self-signed local certs don't need to be trusted separately first
- Writes an error and returns nothing if the login form can't be parsed or the credentials are rejected - check for a `null`/empty session before reusing it

**`New-SPESession` does *not* call `Set-TrustPolicy` for you** - unlike
`New-SitecoreSession` above, connecting via `New-SPESession` against a
self-signed HTTPS endpoint needs the cert-trust override applied explicitly
first (the same `ICertificatePolicy` override `launcher.ps1`'s
`Set-CertificatePolicy` sets up):

```powershell
Add-Type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) { return true; }
}
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
[Net.ServicePointManager]::SecurityProtocol = "Tls, Tls11, Tls12, Ssl3"
```

**This has to be set in the *same* PowerShell process as `New-SPESession`
and every `Invoke-RemoteScript` call that follows it** - `ServicePointManager`
state doesn't persist across separate process invocations. Concretely, this
bit two things live: (1) an agent/automation tool that runs each PowerShell
command as its own fresh process must set the policy, connect, *and* run
`Invoke-RemoteScript` all inside one script/one invocation, not across
several separate tool calls sharing "the same session" only by variable name;
(2) `ServerCertificateValidationCallback = { $true }` (the modern .NET
equivalent) fails differently and unhelpfully in this context - `There is
no Runspace available to run scripts in this thread` - because the callback
runs on a thread with no PowerShell runspace attached. Use the classic
`ICertificatePolicy` override above, not the callback, for this specific
combination.

## Plain-string SPE password

`New-SPESession -Password` takes a plain string, unlike the HTTP `New-SitecoreSession` SecureString. Passing a SecureString to SPE stringifies it as `System.Security.SecureString` and authentication fails.

## Server prerequisites

SPE Minimal and Remoting must be installed and enabled on the target. `Register-SPE -SitecorePath <webroot>` installs these packages, enables the `remoting`/`fileDownload` services, and adds an administrator-role authorization entry alongside the default `sitecore\PowerShell Extensions Remoting` role. This changes server packages and access: obtain explicit authorization before running it; do not enable services or broaden roles to work around a denied connection.
