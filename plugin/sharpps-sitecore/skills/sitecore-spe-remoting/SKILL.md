---
name: sitecore-spe-remoting
description: Connect to Sitecore using SPE Remoting or SharpPS HTTP login. Use for New-SPESession, Invoke-RemoteScript, New-SitecoreSession, installing SPE client modules, self-signed certificate errors, or remoting authentication failures.
---

# Sitecore connections and SPE Remoting

Use this for connection setup, not template design or serialization.

## Workflow

1. Confirm the instance URL and authorized operation. Resolve credentials
   using [sitecore-solution-config](../sitecore-solution-config/SKILL.md).
   Never print credentials; stop on authentication failure and ask for
   corrected values rather than retrying defaults.
2. Check the solution launcher and installed modules. `SharpPS.Shells` and
   the SPE remoting client are separate packages. Module installation and
   the launcher have machine side effects; inspect before running.
3. Choose the connection:
   - HTTP admin pages: `New-SitecoreSession`, **SecureString** password;
     check the returned WebRequestSession is nonempty.
   - Remote item scripts: `New-SPESession`, **plain string** password,
     then `Invoke-RemoteScript`.
4. Run a read-only connectivity check before a requested write. SPE must
   already be installed, enabled, and authorized on the server; do not
   silently enable remoting or broaden roles to fix a failed connection.
5. Before live writes, require explicit user authorization for the target
   and changes. Never self-edit harness permissions or switch tools to
   bypass a denial. If blocked, stop and report it.

## Lookup

| Need | Reference |
|---|---|
| Launcher, non-admin CurrentUser install, missing SPE client | [Module bootstrap](references/connection.md#bootstrap-the-powershell-module-first) |
| HTTP session, SPE certificate setup, same-process requirement | [Connection recipes](references/connection.md#logging-into-a-sitecore-instance) |
| SecureString vs plain-string password | [SPE password](references/connection.md#plain-string-spe-password) |
| Register-SPE and server access changes | [Server prerequisites](references/connection.md#server-prerequisites) |
| Live-write permission boundary | [Harness permissions](references/connection.md#running-this-from-claude-code-specifically) |

Certificate-trust overrides in the legacy recipe are for explicitly
approved, isolated development endpoints only. Prefer valid certificates;
never disable certificate validation for arbitrary or production hosts.

## Related skills

- [sitecore-template-items](../sitecore-template-items/SKILL.md): item creation.
- [sitecore-unicorn-serialization](../sitecore-unicorn-serialization/SKILL.md): export/download.
- [sitecore-runtime-config](../sitecore-runtime-config/SKILL.md): merged configuration lookup.
