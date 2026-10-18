---
name: decompile-dll
description: Decompile or inspect .NET DLL/EXE assemblies with ilspycmd (ILSpy), including headless alternatives to dotPeek/dnSpy, NuGet assembly acquisition, version-isolated dependencies, single-type output, project output, and resources.
---

# Decompile .NET assemblies

Use for authorized inspection of compiled .NET Framework/Core/5+ assemblies.
This skill does not execute the target assembly or require a Liferay checkout.

## Workflow: Spec → Plan → Execution

1. **Spec:** confirm product, product version, assembly, and decompile mode:
   stdout, full project, single type, or resources. Ask for missing inputs.
   Resolve the workspace-parent `decompiler/` root fresh each session;
   never reuse a hardcoded machine path.
2. Inspect `<product>/<product-version>/bin/` for the target and dependencies.
   All assemblies from that product version share this `bin/`; never mix
   versions or create a separate dependency folder per assembly.
3. If acquisition is needed, identify the actual NuGet package/version/TFM.
   Product and package versions are not universally identical. Resolve the
   real global-packages cache rather than assuming `~/.nuget/packages`.
4. **Plan:** state exact restore/copy/install/decompile commands and paths
   before execution. Review the trusted project and obtain approval before
   modifying existing package references, installing a tool, or replacing
   output. Preserve unrelated workspace files.
5. **Execution:** run only the agreed commands. Keep restored assemblies in
   the shared versioned `bin/`, output under the assembly's own directory,
   and use `-r` for dependency resolution where supported by the chosen mode.
6. Report artifacts or inspection results. Missing dependency types require
   the matching DLLs in `bin/`; generated C# is not guaranteed to compile,
   especially with obfuscation/optimization. Treat extracted files as untrusted.

## Lookup

| Need | Reference |
|---|---|
| Dynamic root, product/version layout, restore/cache/dependency acquisition | [Assembly layout and acquisition](references/assembly-layout-and-acquisition.md) |
| Tool choice/install/PATH, stdout/project/type/resource commands, limitations | [ilspycmd workflow](references/ilspycmd-workflow.md) |

Check installed tool help/runtime requirements before relying on historical
flags; documentation restructuring does not verify an ilspycmd installation.

## Related skills

- [Package roles and evidence boundaries](../dotnet-service-registration/references/packages-and-evidence.md): verify SharpPS package roles and historical source scope before interpreting decompiled implementations.
