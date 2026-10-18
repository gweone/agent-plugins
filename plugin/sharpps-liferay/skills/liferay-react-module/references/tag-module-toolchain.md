# Tag-mounted React npm and Gradle wiring

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

## 3. Pattern B: React mounted from a custom tag (modules/search skeleton)

There's no blade template for this one — it's assembled by hand. Use `modules/search` as the
literal reference; the five pieces:

1. **`package.json`** — declares the npm package name used in tag-side component descriptors
   (`"{Component} from <name>"`), Clay + React as deps, `@liferay/npm-scripts` as the dev
   dependency and build tool:
   ```json
   {
     "name": "your-module-name",
     "main": "js/index.ts",
     "dependencies": { "react": "*", "react-dom": "*", "@clayui/...": "*" },
     "devDependencies": { "@liferay/npm-scripts": "*" },
     "scripts": {
       "build": "liferay-npm-scripts build",
       "format": "liferay-npm-scripts format",
       "test": "liferay-npm-scripts test"
     }
   }
   ```
2. **`npmscripts.config.js`** — points at the real TS entry point and, critically, maps
   `react`/`react-dom` to Liferay's own shared frontend module instead of letting them get
   bundled — the TypeScript-toolchain equivalent of pattern A's `--external` flags:
   ```js
   module.exports = {
     build: {
       imports: { '@liferay/frontend-js-react-web': ['react', 'react-dom'] },
       main: './src/main/resources/META-INF/resources/js/index.ts',
     },
   };
   ```
3. **`src/main/resources/META-INF/resources/js/index.ts`** — the barrel export every tag-mounted
   component must be re-exported from; this is what `"{ExportName} from your-module-name"`
   resolves against at mount time.
4. **`bnd.bnd`** — needs `Web-ContextPath`, and — only if any tag is *also* invoked from JSP/FTL
   via a `.tld` (not required just to use `ReactRenderer` itself) — the `jsp.taglib`
   `Provide-Capability` header, per [custom tag registration](../../liferay-custom-taglib/SKILL.md).
5. **`build.gradle`** — apply `com.liferay.node` and wire the npm build's output into the JAR:
   ```groovy
   apply plugin: "com.liferay.node"

   task copyNpmBuild(type: Copy, dependsOn: packageRunBuild) {
       from("build/node/packageRunBuild/resources") {
           include "**/*.js"
           include "**/*.json"
       }
       into "build/resources/main/META-INF/resources"
   }

   jar {
       dependsOn copyNpmBuild
   }
   ```

Then the Java-side tag class uses `ReactRenderer` + `Snapshot<ReactRenderer>` to mount a
component into a placeholder div — that part, plus the shared-parent-div mounting pitfall and
`dangerouslySetInnerHTML`/`html-react-parser` guidance, is covered in [liferay-react-taglib](../../liferay-react-taglib/SKILL.md). Don't duplicate that here — read it there once npm/module wiring is in place.

### Gotcha: `tsconfig.json.disabled`

`modules/search` ships a fully-formed `tsconfig.json` renamed to `tsconfig.json.disabled`
(strict mode, `jsx: react`, scoped to the module's own `js/**/*`). `npmscripts.config.js`'s
`build.main` doesn't reference a tsconfig at all — `liferay-npm-scripts build` transpiles TS
without needing a project-level `tsconfig.json` present. So its `.disabled` suffix doesn't
affect the build either way; rename it to `tsconfig.json` locally only if you want your editor's
TS language server to type-check the module — don't assume you need to "fix" or enable it to get
a working build.

---
