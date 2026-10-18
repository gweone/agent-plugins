# Runtime merged configuration lookup

Use the HTTP login recipe in [Sitecore connections](../../sitecore-spe-remoting/references/connection.md#logging-into-a-sitecore-instance). Resolve credentials from [solution configuration](../../sitecore-solution-config/SKILL.md); check the returned session is nonempty before fetching admin pages. Treat merged configuration as sensitive; return only the relevant redacted settings.

## Reading the live merged configuration

The fully patched/merged runtime `Sitecore.config` (every `App_Config\Include`
patch applied) is available at `/sitecore/admin/showconfig.aspx` - it needs
an authenticated session, i.e. the `$webSession` from `New-SitecoreSession`:

```powershell
$webSession = New-SitecoreSession -Url $Url -Username $Username -Password $securePassword
$config = Invoke-WebRequest -Uri "$Url/sitecore/admin/showconfig.aspx" -WebSession $webSession -UseBasicParsing
```

Use this to verify a config patch actually made it into the merged result
instead of assuming from the source `.config` file on disk - e.g.
`Get-UnicornAutoPublish` fetches this page and regex-matches for
`TriggerAutoPublishSyncedItems` to confirm `Unicorn.AutoPublish.config`'s
patch is live, since that's what actually drives auto-publish after a
Unicorn sync (a plain `Publisher().Publish()` call, like `dbbrowser.aspx`
triggers, does not pick up Unicorn-synced items on its own).
