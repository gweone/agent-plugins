# Container choice and whole React portlet scaffolding

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

## 0. First: does this even need a traditional module?

Check the current workspace's version first — don't assume it. Read `liferay.workspace.product`
(and/or `target.platform.version`) from the root `gradle.properties`:

- **Version < 7.4**: no Client Extension bias applies — a traditional OSGi module is the normal
  default, so choose a [mounting pattern below](module-choice-and-portlet.md).
- **Version ≥ 7.4, or a Quarterly Release (a `liferay.workspace.product` value containing
  `.qN.` / a `dxp-YYYY.qN.x` pattern)**: the consuming workspace's own `CLAUDE.md`-style rules (if present)
  typically bias toward Client Extensions (Custom Element in particular) over traditional OSGi
  modules — check for such a rule before scaffolding, and only fall back to a traditional module
  for the reasons below.

**A traditional module is still the right call when:**
- React needs to be mounted from inside a **JSP or FTL custom tag** (a Display Template, an
  admin JSP) — Client Extensions have no JSP/FTL rendering model at all, so this is a hard
  requirement, not a preference call. See [React taglib mounting](../../liferay-react-taglib/SKILL.md).
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
(see [React taglib mounting](../../liferay-react-taglib/SKILL.md)) is irrelevant to pattern A, which just does a plain
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
  compare against the [`modules/search`-style Gradle wiring](tag-module-toolchain.md) if `npm run build`'s output
  isn't landing in `build/resources/main/META-INF/resources` automatically; you may need to add
  that wiring by hand for this template as generated.
- **`SamplePortlet.java`** — a bare `MVCPortlet` subclass; no Java-side React integration needed
  at all for this pattern (contrast with pattern B, which needs `ReactRenderer`/`Snapshot`).
