---
name: decompile-dll
description: Use when the user wants to decompile a .NET DLL/EXE (.NET Framework or .NET Core/5+) back to C# source — mentions "decompile", "dotPeek", "dotpeek", "ilspy", "ilspycmd", or wants to inspect the source of a compiled assembly (often one of many DLLs shipped by a NuGet-distributed product like Sitecore). Covers resolving/acquiring the target DLL via `dotnet restore` + the NuGet cache into a dynamically-resolved `decompiler/{product}/{product-version}/` layout (never a hardcoded path) — where `{product}` is the actual product, not a NuGet package id, and `bin/` is shared across every assembly decompiled from that same product version — and the ilspycmd CLI workflow, which works on any OS (Windows, Linux, macOS) with the .NET SDK/runtime installed — including headless/remote environments where dotPeek/dnSpy's Windows-only GUI isn't an option.
---

# Decompiling .NET DLLs with ilspycmd

## Source Root & Assembly Layout

Decompilation targets are **not worked on from an arbitrary ad-hoc path** — they live in a
dynamically-resolved location, following the same convention as this plugin family's
`liferay-portal-source` skill (never a hardcoded absolute path, resolved fresh every session):

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

Each assembly is distributed as its own NuGet package (the package id is usually, but not
always, the same as the assembly name — e.g. the `Sitecore.Kernel` package ships
`Sitecore.Kernel.dll`). If `$DECOMPILER_ROOT/<product>/<product-version>/bin/<Assembly>.dll`
already exists, use it as-is and skip straight to decompiling. Otherwise, populate it via NuGet
rather than asking the user to hunt down/upload the DLL by hand:

1. Confirm or create a throwaway project/solution file that references the NuGet package for the
   target assembly, pinned to `<product-version>` (reuse a project the user already has if it
   references that package; add the package reference if it doesn't).
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
   DLLs — needed later for `-r`) from `<global-packages-path>/<package-id>/<product-version>/lib/<tfm>/*.dll`
   into the **shared** `$DECOMPILER_ROOT/<product>/<product-version>/bin/`.

Only decompile from `bin/` once it's populated this way — this keeps every assembly belonging to
one product+version, and the eventual decompiled output for each, all addressed by the same
`$DECOMPILER_ROOT/<product>/<product-version>/` root instead of scattered ad-hoc paths. When the
user asks for a second assembly from a product+version you've already set up, reuse the existing
`bin/` — only restore/copy the newly-needed package into it, not a whole fresh `bin/`.

## Workflow

This skill follows the plugin's standard **Spec → Plan → Execution** convention — never jump
straight to running `dotnet restore`/`ilspycmd`:

1. **Spec** — resolve `$DECOMPILER_ROOT/<product>/<product-version>` and check whether `bin/`
   already has the target DLL. If not, resolve the solution/project file to restore from. Also
   settle the decompile mode: single-file stdout dump vs. a full project directory (`-p -o`), a
   single type only (`-t`), or a resource listing/extraction. Ask the user if any of this is
   ambiguous rather than guessing.
2. **Plan** — state the exact commands that will run, in order — the `dotnet restore` +
   copy-into-`bin/` steps if the DLL isn't already there, then the exact `ilspycmd` command
   (including its `-o`/`-r` paths) — before running any of it, so the user can see what will be
   written to disk.
3. **Execution** — run the commands from the Plan and report what was produced (restored/copied
   DLLs, then the stdout dump, files written under the output directory, or the resource/type
   list).

## Why ilspycmd

`dotPeek` and `dnSpy` are Windows-only desktop GUI apps (dotPeek requires Windows 10/11 or
Windows Server 2019/2022 + .NET Framework 4.7.2+; JetBrains ships no CLI/Linux/macOS build of
dotPeek, unlike their other dotUltimate tools). They're fine choices **if** the user is on
Windows with desktop/GUI access. Use **ilspycmd** instead whenever that's not the case — a
headless or remote Linux/macOS box, a Windows Server without desktop access, CI, or just when a
scriptable CLI is preferred over a GUI. It's the CLI decompiler built on the same
ICSharpCode.Decompiler engine (ILSpy) and runs identically on **any OS with the .NET
SDK/runtime installed — Windows, Linux, or macOS**.

## Tool

`ilspycmd` is installed as a dotnet global tool, the same way on every OS:

```bash
dotnet tool install -g ilspycmd
```

- **Linux/macOS**: it lives in `~/.dotnet/tools`. Most shells need this added to `PATH`
  manually (`export PATH="$PATH:$HOME/.dotnet/tools"` in `~/.bashrc`/`~/.zshrc`) — check with
  `ilspycmd --version` first; if a non-login shell doesn't see it, invoke `bash -lc 'ilspycmd ...'`.
- **Windows**: it lives in `%USERPROFILE%\.dotnet\tools`. The `dotnet tool install -g` installer
  normally adds this to the user `PATH` automatically; if `ilspycmd` isn't found, open a new
  terminal (PATH changes don't apply to already-open shells) or add it manually.

It decompiles **both .NET Framework (2.0–4.8.x) and .NET Core/5+ assemblies** —
reads CIL/metadata directly, doesn't care which framework produced it or which OS it's running on.

## Common commands

`$ASSEMBLY` = `$DECOMPILER_ROOT/<product>/<product-version>/bin/<Assembly>.dll`, `$BIN` = its
`bin/` folder, `$OUT` = `$DECOMPILER_ROOT/<product>/<product-version>/<assembly-name>/`. Shown
with forward-slash paths; on Windows these work equally well with backslash paths in PowerShell
or cmd.

```bash
# Dump decompiled C# to stdout (single file, quick look)
ilspycmd "$ASSEMBLY"

# Dump to a directory, one C# file per type, as a compilable project
ilspycmd -p -o "$OUT" -r "$BIN" "$ASSEMBLY"

# Same, but nest output into folders matching namespaces
ilspycmd --nested-directories -p -o "$OUT" -r "$BIN" "$ASSEMBLY"

# Decompile just one type
ilspycmd -t Namespace.ClassName -o "$OUT" -r "$BIN" "$ASSEMBLY"

# List all types (classes/interfaces/structs/enums/delegates)
ilspycmd -l c,i,s,d,e "$ASSEMBLY"

# List embedded resources (incl. BAML entries inside .g.resources for WPF)
ilspycmd "$ASSEMBLY" --list-resources

# Extract one resource (BAML auto-converts to XAML)
ilspycmd "$ASSEMBLY" --resource Assembly.g.resources/mainwindow.baml -o "$OUT"
```

Always pass `-r "$BIN"` once `bin/` has been populated (see above) — that's what resolves
references to the target's dependency DLLs instead of leaving them unresolved.

## Notes

- If `bin/` is missing some of the target's dependency DLLs (e.g. it has
  `Sitecore.Kernel.dll` but the target references `Sitecore.ContentSearch.dll`, which hasn't
  been restored into this product+version's `bin/` yet), those member/type references show as
  unresolved even with `-r` — restore/copy the missing dependency into the same shared `bin/`
  folder and re-run, rather than treating it as an ilspycmd limitation.
- `-p` requires `-o`; without `-p`, `-o` still writes one flat `.cs` file
  instead of printing to stdout.
- Output is not guaranteed to compile as-is for obfuscated or heavily
  optimized assemblies, but is reliable for standard Release-build
  .NET Framework/.NET Core assemblies (e.g. Sitecore, or any other NuGet-distributed product).
- Behavior is identical across OSes — the same flags and output apply whether `ilspycmd` runs
  on Windows, Linux, or macOS. The only OS-specific differences are the tool-install PATH steps
  above and native path-separator conventions.
