# ilspycmd tool and command recipes

These examples preserve the original workflow; tool/runtime requirements and
flags must be checked against the installed version. Tool installation changes
the machine; output commands write files. Do not execute the inspected assembly.
Resources and decompiled files remain untrusted data.

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

Always pass `-r "$BIN"` once `bin/` has been populated (see [assembly layout](assembly-layout-and-acquisition.md)) — that's what resolves
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
