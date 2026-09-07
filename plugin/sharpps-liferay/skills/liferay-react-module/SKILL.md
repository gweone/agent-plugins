---
name: liferay-react-module
description: Use whenever the user wants to set up, scaffold, or add React support to a traditional Liferay OSGi module — "how do I set up a React module", "npm-react-portlet", "how do I get a React component rendering in Liferay", "esbuild liferay portlet", "liferay-npm-scripts", "@liferay/frontend-js-react-web", or any work touching a module's package.json/npmscripts.config.js/build.gradle for bundling React/TypeScript into a portlet or custom tag. Covers whether a traditional module is even the right container (vs. a Client Extension) before scaffolding, and the two patterns seen in this workspace: a whole React-driven portlet (blade's `npm-react-portlet` template) vs. React mounted from a custom JSP/FTL tag (`modules/search`, a.k.a. sharpps-search). For the Java-side tag mechanics of the second pattern, see the companion `liferay-taglibs` skill's Section 6 — this skill covers getting npm/React wired into the module, not the tag-mounting API.
---

# Liferay React Module Skill

## Workflow

This skill follows the plugin's standard **Spec → Plan → Execution** convention — never jump
straight to running `blade create` or `blade gw deploy`:

1. **Spec** — resolve the concrete target before doing anything: does this even need a
   traditional module (Section 0), and if so, which pattern, A or B (Section 1)? Ask the user if
   it's ambiguous rather than guessing.
2. **Plan** — once the pattern is settled, state out loud the exact scaffold command (Section 2's
   `blade create ...`, or the files Section 3 will hand-assemble) and the exact deploy command
   (Section 4's `blade gw :modules:<name>:deploy`), including the module name/package, *before*
   running either.
3. **Execution** — run the scaffold step, then the build/deploy step, from that Plan.

## 0. First: does this even need a traditional module?

Check the current workspace's version first — don't assume it. Read `liferay.workspace.product`
(and/or `target.platform.version`) from the root `gradle.properties`:

- **Version < 7.4**: no Client Extension bias applies — a traditional OSGi module is the normal
  default, so skip straight to Section 1.
- **Version ≥ 7.4, or a Quarterly Release (a `liferay.workspace.product` value containing
  `.qN.` / a `dxp-YYYY.qN.x` pattern)**: this workspace's own `CLAUDE.md`-style rules (if present)
  typically bias toward Client Extensions (Custom Element in particular) over traditional OSGi
  modules — check for such a rule before scaffolding, and only fall back to a traditional module
  for the reasons below.

**A traditional module is still the right call when:**
- React needs to be mounted from inside a **JSP or FTL custom tag** (a Display Template, an
  admin JSP) — Client Extensions have no JSP/FTL rendering model at all, so this is a hard
  requirement, not a preference call. See `liferay-taglibs` skill, Section 6.
- You need a full **MVC portlet** (its own `javax.portlet.name`, portlet preferences,
  `RenderRequest`/`ActionRequest` lifecycle) with React only as the view's rendering layer.

**Reach for a Custom Element Client Extension instead when** the React app is a standalone
widget that just needs to be droppable onto a page via Fragments/Widgets — no JSP/FTL
integration and no portlet lifecycle needed. Don't scaffold a traditional module for that case.

If unsure which applies, ask the user what the React component needs to render *inside* (a page
widget vs. a specific tag's output inside an existing JSP/FTL) before picking a path.

---

## 1. Two concrete patterns — pick based on where React mounts

| | **A. Whole portlet is React** | **B. React mounted from inside a tag** |
|---|---|---|
| Real example | `blade create -t npm-react-portlet` (verified by generating one) | `modules/search` (`sharpps-search`) |
| Bundler | esbuild, plain JS | `@liferay/npm-scripts`, TypeScript |
| Where React mounts | Portlet's own `view.jsp`, whole `<div>` | A custom tag's placeholder `<div>`, via `ReactRenderer` |
| React/react-dom | Marked `--external`, own version pinned in `package.json` | Resolved to Liferay's shared copy via `imports` in `npmscripts.config.js` |
| Use when | The portlet's entire view is a React app | React is one piece embedded in JSP/FTL markup alongside other server-rendered content |

Don't mix these up — pattern B's `ReactRenderer`/`Snapshot`/`ComponentDescriptor` machinery
(see `liferay-taglibs` Section 6) is irrelevant to pattern A, which just does a plain
`ReactDOM.render()` into a div the portlet's own JSP already owns.

---

## 2. Pattern A: whole portlet is React (blade scaffold)

Scaffold it with blade rather than hand-copying files, run from the target workspace's root (not
via `-d` pointed elsewhere). State the resolved package name and module name (the Plan) before
running:

```bash
blade create -t npm-react-portlet -p com.example.yourpackage your-module-name
```

Don't pass `-v`/`--liferay-product` — verified live that `blade create`, run from inside a real
workspace root, auto-detects the product/version from that workspace itself and generates the
correct dependency accordingly (a DXP workspace yielded
`compileOnly group: "com.liferay.portal", name: "release.dxp.api"` in the generated
`build.gradle`, with no flag needed). Only fall back to an explicit `-v <version>` /
`--liferay-product <portal|dxp>` if blade errors with "Cannot determine Liferay Version" — that
happens when it can't see a real workspace context (e.g. `-d` pointed outside one), not under
normal use.

This generates, verified by actually running it:

- **`package.json`** — pins `react`/`react-dom` versions directly, adds `esbuild` as a dev
  dependency, and defines the build script inline:
  ```json
  "scripts": {
    "build": "esbuild ./src/main/resources/META-INF/resources/js/index.js --bundle --outfile=./build/resources/main/META-INF/resources/js/index.js --loader:.js=jsx --format=esm --external:react --external:react-dom"
  }
  ```
  `--external:react --external:react-dom` is load-bearing — it keeps this module's bundle from
  shipping its own copy of React. **Never remove this** to "simplify" the build: two separate
  React copies loaded on the same page is the classic cause of "Invalid hook call" / duplicate
  context errors. Liferay's portal-wide shared React (from `frontend-js-react-web`) is what
  resolves the bare `react`/`react-dom` specifiers at runtime instead.
- **`view.jsp`** — an empty mount `<div>` plus an `<aui:script>` that dynamically `import()`s the
  built bundle by its deployed URL and calls the module's default export:
  ```jsp
  <div id="<portlet:namespace />-root"></div>
  <aui:script>
      import(
          Liferay.ThemeDisplay.getPathContext() + '/o/your-module-name/js/index.js'
      ).then(
          (module) => module.default('<portlet:namespace />-root')
      );
  </aui:script>
  ```
- **`js/index.js`** — plain React, default-exports a `function(elementId)` that does
  `ReactDOM.render(<App />, document.getElementById(elementId))`. Replace the generated
  tic-tac-toe sample with your real component; keep the `export default function(elementId)`
  shape since `view.jsp` calls it positionally.
- **`bnd.bnd`** — just `Web-ContextPath` + `Export-Package` for the portlet-keys constant class
  + language resource capability. Nothing React-specific here — the JS bundling is entirely a
  Gradle/npm build-time concern, not an OSGi manifest concern.
- **`build.gradle`** — plain `compileOnly` on `release.portal.api`/`release.dxp.api`. Note this
  generated one does **not** include the `com.liferay.node` plugin or a `copyNpmBuild` task —
  compare against `modules/search`'s `build.gradle` (Section 3) if `npm run build`'s output
  isn't landing in `build/resources/main/META-INF/resources` automatically; you may need to add
  that wiring by hand for this template as generated.
- **`SamplePortlet.java`** — a bare `MVCPortlet` subclass; no Java-side React integration needed
  at all for this pattern (contrast with pattern B, which needs `ReactRenderer`/`Snapshot`).

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
   `Provide-Capability` header, per `liferay-taglibs` Section 4.
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
`dangerouslySetInnerHTML`/`html-react-parser` guidance, is fully covered in `liferay-taglibs`
Section 6. Don't duplicate that here — read it there once npm/module wiring is in place.

### Gotcha: `tsconfig.json.disabled`

`modules/search` ships a fully-formed `tsconfig.json` renamed to `tsconfig.json.disabled`
(strict mode, `jsx: react`, scoped to the module's own `js/**/*`). `npmscripts.config.js`'s
`build.main` doesn't reference a tsconfig at all — `liferay-npm-scripts build` transpiles TS
without needing a project-level `tsconfig.json` present. So its `.disabled` suffix doesn't
affect the build either way; rename it to `tsconfig.json` locally only if you want your editor's
TS language server to type-check the module — don't assume you need to "fix" or enable it to get
a working build.

---

## 4. Building and deploying either pattern

Same as any other module in a Liferay workspace — steer toward blade, not raw `gradlew`. State
the exact module path (the Plan) before running:

```bash
blade gw :modules:your-module-name:deploy
```

This runs the module's npm build as part of the Gradle build (via whichever wiring from
Section 2/3 applies) and deploys the resulting JAR to the running server's
`osgi/modules` — watch `bundles/tomcat/logs/catalina.out` for
`STARTED [your.bundle.symbolic.name]` to confirm the OSGi bundle actually came up.
