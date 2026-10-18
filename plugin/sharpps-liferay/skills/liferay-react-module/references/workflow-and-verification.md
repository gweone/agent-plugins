# React module workflow and verification evidence

[Skill workflow and reference index](../SKILL.md)

> Evidence scope: retained from source tracing and live debugging in an earlier consuming
> Liferay workspace, not executed or re-verified in this plugin repository. Resolve the
> current workspace, target release and applicable local rules before applying examples.
> `modules/search` (`sharpps-search`), `client-extensions/liferay-global-extension`,
> initializer paths, `.claude/rules/cx.md`/`CLAUDE.md`, `configs/local`, `bundles`, and
> container `liferay-dev` are external workspace examples, not plugin-local files or links.
> Resolve `$LIFERAY_PORTAL` with [liferay-portal-source](../../liferay-portal-source/SKILL.md)
> for source citations; line numbers describe the inspected snapshot, not every release.
> Headings retain original numbering for provenance; navigation uses topical links.

## Workflow

This skill follows the plugin's standard **Spec → Plan → Execution** convention — never jump
straight to running `blade create` or `blade gw deploy`:

1. **Spec** — resolve the concrete target before doing anything: does this even need a
   traditional module and, if so, [which mounting pattern, A or B](module-choice-and-portlet.md)? Ask the user if
   it's ambiguous rather than guessing.
2. **Plan** — once the pattern is settled, state out loud the exact [portlet scaffold command](module-choice-and-portlet.md)
   (`blade create ...`), or the [tag-module files to hand-assemble](tag-module-toolchain.md) and the exact deploy command
   (`blade gw :modules:<name>:deploy`, described below), including the module name/package, *before*
   running either.
3. **Execution** — run the scaffold step, then the build/deploy step, from that Plan.

## 4. Building and deploying either pattern

Same as any other module in a Liferay workspace — steer toward blade, not raw `gradlew`. State
the exact module path (the Plan) before running:

```bash
blade gw :modules:your-module-name:deploy
```

This runs the module's npm build as part of the Gradle build (via whichever wiring from
[portlet](module-choice-and-portlet.md) or [tag-module](tag-module-toolchain.md) wiring applies) and deploys the resulting JAR to the running server's
`osgi/modules` — watch `bundles/tomcat/logs/catalina.out` for
`STARTED [your.bundle.symbolic.name]` to confirm the OSGi bundle actually came up.

Commands above are retained historical workflow examples, not authorization to run
scaffolding, builds or deployment. Resolve the consuming workspace and obtain the
required user approval before any such action.
