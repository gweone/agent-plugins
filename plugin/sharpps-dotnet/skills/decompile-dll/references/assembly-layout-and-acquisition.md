# Assembly layout and NuGet acquisition

This is a workflow for authorized source inspection, not permission to restore
packages or modify an existing project. Inspect destinations before replacing
files; keep versions isolated.

## Source Root & Assembly Layout

Decompilation targets are **not worked on from an arbitrary ad-hoc path** — resolve the
current workspace root fresh every session and use its parent as the shared projects root.
The `decompiler/` directory is a sibling of the workspace, never a hardcoded absolute path:

```bash
# The current workspace's git top-level (falls back to pwd if not inside a git repo).
WORKSPACE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# The shared "projects" directory one level up — the same root that houses the
# current repo/workspace itself, so decompiler/ ends up as a sibling of it.
PROJECTS_ROOT="$(dirname "$WORKSPACE_ROOT")"

DECOMPILER_ROOT="$PROJECTS_ROOT/decompiler"
```

Layout, per product and version:

```
$DECOMPILER_ROOT/
└── <product>/                 # the actual product, e.g. "Sitecore" — NOT a NuGet package id
    └── <product-version>/     # e.g. 10.3.1
        ├── bin/                # ALL restored DLLs for this product+version, shared across
        │                       # every assembly decompiled from it — also the -r reference folder
        ├── <assembly-name>/    # decompiled C# output for one assembly (the ilspycmd -o target)
        └── <other-assembly>/   # a second assembly from the SAME product+version, same bin/
```

Resolve `<product>` and `<product-version>` from the user's request; ask if either is ambiguous
rather than guessing. `bin/` is keyed by product+version, **not** by assembly — a product
release ships many assemblies (e.g. Sitecore ships `Sitecore.Kernel.dll`,
`Sitecore.ContentSearch.dll`, `Sitecore.Mvc.dll`, ...), and they all belong in the same shared
`bin/` for that version, since they commonly reference each other. This also means the same
assembly can be decompiled once per product version it's needed for — `<product-version>` is the
isolation boundary, not `<assembly-name>` — so e.g. `Sitecore.Kernel.dll` from 10.1 and from
10.3 land in two separate `bin/`/output trees and never mix.

### Getting the DLL: `dotnet restore` + NuGet cache, not a manual download

For the NuGet-distributed targets described here, locate the package that actually ships
the assembly (its ID is often, but not always, the assembly name — e.g. the `Sitecore.Kernel` package ships
`Sitecore.Kernel.dll`). If `$DECOMPILER_ROOT/<product>/<product-version>/bin/<Assembly>.dll`
already exists, use it as-is and skip straight to decompiling. Otherwise, populate it via NuGet
rather than asking the user to hunt down/upload the DLL by hand:

1. Confirm or create a throwaway project/solution file that references the NuGet package for the
   target assembly, pinned to the verified package version for `<product-version>`. Product
   and NuGet package versions need not match; confirm the actual package version/TFM.
   Reuse a trusted existing project only if appropriate, and obtain approval before
   adding or modifying its package references.
2. Restore it — this downloads the package into the local NuGet cache, not into the project
   folder:
   ```bash
   dotnet restore path/to/Solution.sln
   ```
3. Find the actual NuGet global-packages folder — **don't hardcode `~/.nuget/packages`**, it can
   be overridden by the `NUGET_PACKAGES` env var or a `nuget.config`:
   ```bash
   dotnet nuget locals global-packages --list
   ```
4. Copy the restored assembly (and, the first time for a given product+version, its dependency
   DLLs — needed later for `-r`) from `<global-packages-path>/<package-id>/<verified-package-version>/lib/<tfm>/*.dll`
   into the **shared** `$DECOMPILER_ROOT/<product>/<product-version>/bin/`.

Only decompile from `bin/` once it's populated this way — this keeps every assembly belonging to
one product+version, and the eventual decompiled output for each, all addressed by the same
`$DECOMPILER_ROOT/<product>/<product-version>/` root instead of scattered ad-hoc paths. When the
user asks for a second assembly from a product+version you've already set up, reuse the existing
`bin/` — only restore/copy the newly-needed package into it, not a whole fresh `bin/`.
