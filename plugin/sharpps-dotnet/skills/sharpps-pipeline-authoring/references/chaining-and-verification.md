# Chaining pipelines and verification

Historical external source/version guidance, not newly verified runtime. `docker`/`deploy`
and helpers below are examples from a source/workspace version; confirm they exist in the
installed module. **Spec → Plan → Execution:** name files, host/session, pipelines, arguments,
predecessors, targets, and verification fixtures. Get explicit authorization for effects before
running commands. Never install/trust/bypass certificates or touch real deployments, databases,
containers, or software installations merely to validate documentation or an implementation.

## Chaining pipelines

Two mechanisms, both sharing the same `$arguments`:

```powershell
# a) a delegating processor (e.g. Liferay/Frappe forwarding Service/Log/Restart keys to docker):
$isVerbose = $VerbosePreference -eq "Continue"
Start-Pipeline docker -Verbose:$isVerbose -Args $arguments

# b) registration-time dependency — every run of this pipeline runs startup first:
Register-Pipeline -BasePath ./Pipelines -Predecessors startup -Force
```

Prefer (a) when only *some* trigger keys should forward; (b) when the other pipeline must
always complete first.

## Verification checklist before calling it done

Plan these checks and run only the authorized ones in an isolated fixture after source review.
They describe the original implementation's verification guidance, not checks already run here.
Module import can initialize code; empty config does not guarantee no effects:

1. `Import-Module ./SharpPS.Shells.psd1 -Force` (or `Register-Pipeline ... -Force`) — parses
   cleanly, pipeline appears.
2. Read `00-Help.ps1`, `Get-Pipeline` output, predecessor chains, and `AlwaysRun` scripts first.
   Then, in an authorized isolated fixture, `Start-Pipeline <name> -Help` should render an
   un-mangled banner matching real keys and abort ordinary later processors. **Do not assert
   nothing else runs:** the engine runs predecessors before setting `Help`; `AlwaysRun` can
   run after abort. Test and document these effects explicitly, including inherited Args flags.
3. `Start-Pipeline <name>` with empty/zero config in an empty directory — every step either
   works or aborts with a message naming the missing key; no unhandled exceptions.
4. Force each failure path (bad build command, missing artifact, wrong container) — verify the
   chain stops where it should and later steps are skipped.
5. The success path end-to-end — but **never against a real target the user didn't ask to
   touch**: simulate the environment-changing part (scratch folders, a byte-identical artifact,
   a background job standing in for the consumer) and leave the first real run to the user.
6. Sweep for leaked specifics: `grep -rin "liferay|sitecore|/opt/|C:\\\\" <new files>` must come
   back empty (examples in help text use neutral placeholders like `myservice`).

## Reference implementation

`SharpPS.VisualStudio/SharpPS.Shells/Pipelines/Deploy/` is the original guidance's worked example — a
stack-neutral hot-deploy loop (resolve config → build → clear container log → copy → poll-verify
by hash → error report) where processors follow the [authoring rules](../SKILL.md) and all real work lives in
public functions (`Clear-DockerLog`, `Get-DeployDrift`, `Find-LogError`).

The registration-time predecessor runs before this pipeline's processors and shares the same
hashtable; delegating calls share `Help`/`Aborted` already present in it. Neither mechanism is
an isolated invocation, transaction, or dry-run. Avoid predecessor cycles and review literal
`Start-Pipeline ...` predecessor command strings as executable code.

- [Engine execution order](../../sharpps-pipeline/references/registration-and-execution.md).
- [Layout/Help convention](layout-and-processors.md).
- [Configuration/failure handling](configuration-and-failure.md).
- [Authoring entrypoint](../SKILL.md).
