# Unicorn export and workspace retrieval

Use [SPE remoting](../../sitecore-spe-remoting/SKILL.md) for an authorized connection. Confirm the target paths/configuration before export and inspect local destination files before replacing them. Maybank paths and the Core.Website configuration below are historical examples, not defaults; resolve the current solution's actual configuration.

### Serializing an item to disk - check for Unicorn first, don't default to `Export-Item`

**Before serializing anything, check whether the solution has Unicorn
configured for the target Sitecore path** - grep the solution for
`physicalRootPath` / `<configurations>` (Unicorn's own serialization config,
typically under an `App_Config/Include/Unicorn/**/*.Serialization.config`
or similarly-named file, one `<configuration name="..."><targetDataStore
physicalRootPath="..."/><predicate>...<include name="..." path="..."/>...`
block per logical grouping). If a `<predicate><include>` covers the path
you just created items under, **that configuration is the solution's real
serialization mechanism for this content** - use it (below), not SPE's own
`Export-Item`. Historical example (SharpPS.Sitecore, not a default for every solution):
this solution used **Unicorn**, confirmed live: its config's `include name="Template.Feature.Maybank" path="/sitecore/
templates/Feature/Maybank"` and `include name="zzz.Content.Maybank" path="/
sitecore/content/Maybank"` map exactly onto this repo's own `items/Core/
Template.Feature.Maybank/...` / `items/Content/zzz.Content.Maybank/...`
folder layout - i.e. **the very YAML format this whole skill has been
reverse-engineering from existing files *is* Unicorn's Rainbow YAML
serialization**, not a bespoke or Sitecore-CLI format. Don't assume "no
`sitecore.json`/`*.module.json` found" means no serialization tooling is
configured - that's the Sitecore CLI's config format, a different (and, in
this solution, absent) mechanism; Unicorn's is XML, not JSON.

**When Unicorn covers the path, use its own SPE bridge cmdlet,
`Export-UnicornItem -Item <item> -Recurse`** (confirmed live, ships as part
of the solution's own Unicorn integration - `Get-Command -Name
"*Unicorn*"` lists it alongside `Sync-UnicornItem`/`Sync-UnicornConfiguration`
etc.), not SPE's own `Export-Item`. `Export-UnicornItem` resolves the
matching configuration automatically from the item's path and writes
through Unicorn's own configured `ITargetDataStore` (Rainbow's
`SerializationFileSystemDataStore`) - guaranteeing the output matches
what a real Unicorn sync would produce, in the exact format/layout already
in the repo, unlike hand-authoring YAML to match the format by eye:

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($itemPath)
    $item = Get-Item -Path $itemPath
    Export-UnicornItem -Item $item -Recurse
} -ArgumentList "master:/sitecore/templates/Feature/$core/$area/$featureName/$renderingName"
```

**Only fall back to SPE's own `Export-Item`** (`Spe.Commands.Serialization.
ExportItemCommand`) when no Unicorn (or equivalent) config covers the
target path at all - it serializes to Sitecore's older classic `.item` text
format via `Sitecore.Data.Serialization.Manager.DumpItem`, a different
format from Rainbow YAML and the wrong choice for a Unicorn-serialized
solution:

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    param($itemPath)
    Get-Item -Path $itemPath | Export-Item -Recurse
} -ArgumentList "master:/sitecore/templates/Feature/$core/$area/$featureName/$renderingName"
```

Both cmdlets write **on the Sitecore instance's own filesystem**, since the
script block runs server-side through `Invoke-RemoteScript` - not on
whatever machine started the SPE session, and (for a genuinely remote
instance, not a local one) not the same filesystem the local git repo lives
on at all. Retrieving the file(s) afterward needs one more step - see
below.

#### Finding where Unicorn actually wrote the files

`$(sourceFolder)`-style tokens in the `.config` file aren't resolved values
- get the real absolute path from the live configuration object instead of
guessing, since it may differ between environments (a remote dev instance's
own checkout path is not necessarily the same as the path on the machine
running these commands):

```powershell
Invoke-RemoteScript -Session $speSession -ScriptBlock {
    $config = Get-UnicornConfiguration | Where-Object { $_.Name -eq "Core.Website" }
    $targetDataStore = $config.Resolve([Unicorn.Data.ITargetDataStore])
    # ITargetDataStore is a ConfigurationDataStore wrapper - the real Rainbow
    # store (and its root path) is one level in, via .InnerDataStore
    $targetDataStore.InnerDataStore.PhysicalRootPath
}
```

**`PhysicalRootPath` is a public field, not a property** - it won't show up
under `Get-Member`/`.GetProperties()` defaults; access it directly
(`$store.PhysicalRootPath`) rather than reflecting for a "PhysicalRootPath"
*property* and getting a silent null back.

#### Filename truncation - a real item name doesn't always match its filename

Rainbow's `SerializationFileSystemDataStore` truncates long item names when
generating the on-disk filename (confirmed live: a field genuinely named
`OTR Price Error Required Message` - 33 characters - serialized to
`OTR Price Error Required Messa.yml`, a 30-character stem before `.yml`;
the item's actual Sitecore `Name` is untouched, only the filename is cut).
This matches this repo's own existing convention (multiple pre-existing
`.yml` filenames in `items/` are exactly 30 characters before the
extension) - so when programmatically locating a just-exported file by
name, don't assume `{item name}.yml` is always the real filename for names
approaching/exceeding ~30 characters; read back the actual directory
listing (`Get-ChildItem`) rather than constructing the expected filename
from the item name for anything long enough to be near that boundary.

#### Retrieving the exported files onto the machine that needs them

If the machine running these commands *is* the Sitecore instance's own
filesystem (a local dev instance), the files are already in place - nothing
more to do. For a genuinely remote instance (its own `Invoke-RemoteScript`
filesystem is not reachable as a local path - confirmed live for a
solution whose actual instance runs on a separate machine from where its
git repo checkout is being edited), retrieve them over the same SPE
Remoting connection rather than assuming file-share access:

- **`Receive-RemoteItem`** (a **local**, client-side SPE cmdlet - not run
  inside `Invoke-RemoteScript`) is the purpose-built tool for this: it
  downloads a file from the server through SPE's own web service endpoint.
  For a plain absolute server-side file path (not a Sitecore media item),
  pass it directly as `-Path` with no `-RootPath` needed (`-RootPath` is
  only for a small fixed set of keyword-relative locations - `App`, `Data`,
  `Media`, `Serialization`, etc. - and is required only when `-Path` isn't
  already a fully-qualified path):

  ```powershell
  Receive-RemoteItem -Session $speSession `
      -Path "C:\Projects\Solution\items\Core\...\SomeField.yml" `
      -Destination "C:\LocalRepo\items\Core\...\SomeField.yml" -Force
  ```

  It also accepts a list of server paths over the pipeline (e.g. from an
  `Invoke-RemoteScript` call that returns matching file paths via
  `Get-ChildItem ... | Select-Object -Expand FullName`), downloading each
  in turn - useful for pulling every file Unicorn just wrote in one step,
  though each still needs its own `-Destination` folder or `-Container` to
  preserve structure. Confirmed live to exist and documented (source:
  https://doc.sitecorepowershell.com/appendix/common/receive-file describes
  `Receive-File`, a *different*, upload-only, interactive-dialog cmdlet
  that doesn't work over `Invoke-RemoteScript` at all - don't confuse the
  two by name similarity; `Receive-RemoteItem` is the download one).
- If `Receive-RemoteItem` isn't available or convenient for the number of
  files involved, the same result is achievable by having
  `Invoke-RemoteScript` itself return each file's content as a string
  (`Get-Content $path -Raw`) and writing it locally from the returned
  value - confirmed live to work end-to-end for dozens of files at once,
  though it's a workaround rather than the purpose-built mechanism above.
  Whichever approach is used, verify the retrieved content against a few
  known-good existing files in the repo afterward (matching field-sharing
  conventions, ID formatting, alphabetical field ordering) rather than
  assuming the transfer preserved everything correctly.
