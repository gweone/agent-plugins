---
name: liferay-portal-source
description: >
  Use this skill whenever the user wants to explore, understand, navigate, search, modify,
  build, debug, or reason about the Liferay Portal source code. The source lives in a
  dynamically-resolved sibling checkout next to the current workspace (never a hardcoded path).
  If no checkout is found there, ask the user whether they already have one elsewhere before
  cloning anything new. Trigger this skill for any question about Liferay modules, portlets,
  OSGi components, service builder entities,
  themes, frontend JS/CSS, Gradle build tasks, upgrade steps, APIs, hooks, fragments, or
  customizations rooted in that codebase. Also trigger when the user says things like "in our
  Liferay source", "in the portal repo", "find the class for X in Liferay", "how does Liferay
  implement X", or asks to make changes to any file inside the Liferay Portal source tree.
---

# Liferay Portal Source Skill

## Source Root

The Liferay Portal source is **not bundled with this skill** and is **never at a fixed path**.
Resolve it fresh at the start of every session, in this order — do not assume any previous
value or a hardcoded absolute path:

### 1. Check the default sibling location

```bash
# The current workspace's git top-level (falls back to pwd if not inside a git repo).
WORKSPACE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# The shared "projects" directory one level up — the same root that houses the
# current repo/workspace itself, so liferay-portal ends up as a sibling of it.
PROJECTS_ROOT="$(dirname "$WORKSPACE_ROOT")"

LIFERAY_PORTAL="$PROJECTS_ROOT/liferay-portal"
```

If `$LIFERAY_PORTAL` already exists there (has a `modules/` or `portal-impl/` dir), use it and
skip straight to orientation below.

### 2. If not found there, ask the user before cloning anything

**Do not silently bootstrap a fresh checkout.** A full Liferay Portal source tree is large and
the user may already have one checked out elsewhere (a different drive, an existing clone from
other work, a specific version/tag they're targeting). Ask first, e.g.:

> "I don't see a `liferay-portal` checkout at `$LIFERAY_PORTAL`. Do you already have one
> somewhere I should use instead? If so, what path?"

- If the user gives a path → set `LIFERAY_PORTAL` to that path instead (validate it looks like
  a real checkout — `modules/`, `portal-impl/`, or `portal-kernel/` should exist under it) and
  use it for the rest of the session.
- If the user confirms they don't have one → proceed to the bootstrap step below.

### 3. Bootstrap only after the user confirms there isn't one already

**Do not run a plain `git clone`** — upstream `liferay/liferay-portal` has 10+ years of history
and a multi-gigabyte `.git` directory, which is far too slow/heavy just to read the source.
Instead, pull only the current tree as a single squashed commit with no retained upstream
history:

```bash
if [ ! -d "$LIFERAY_PORTAL/.git" ]; then
  mkdir -p "$LIFERAY_PORTAL"
  git -C "$LIFERAY_PORTAL" init
  git -C "$LIFERAY_PORTAL" remote add origin https://github.com/liferay/liferay-portal.git
  git -C "$LIFERAY_PORTAL" fetch --depth=1 origin master
  git -C "$LIFERAY_PORTAL" merge --squash origin/master
  git -C "$LIFERAY_PORTAL" commit -m "Import liferay-portal source (squashed, no upstream history)"
fi
```

This yields a shallow, single-commit local repo with just the current source tree — no
multi-GB history is downloaded or kept around. If a specific release is needed (e.g. a DXP tag
or an older `7.x` branch instead of `master`), substitute that ref for `master` in both the
`fetch` and `merge --squash` lines — ask the user which version if it's not already clear from
context.

---

## First Step: Orient Before Acting

Before answering any question or making any change, run a quick orientation if you haven't already:

```bash
# Top-level structure
ls "$LIFERAY_PORTAL"

# Identify the version
cat "$LIFERAY_PORTAL/release.properties" 2>/dev/null \
  || cat "$LIFERAY_PORTAL/portal-impl/src/portal.properties" 2>/dev/null | grep "^build.number" \
  || git -C "$LIFERAY_PORTAL" log --oneline -1
```

Do NOT skip orientation — the layout differs between Liferay 7.0, 7.1, 7.2, 7.3, 7.4, and DXP versions.

---

## Canonical Directory Layout

```
liferay-portal/
├── modules/                    # OSGi bundles (the modern way, Liferay 7+)
│   ├── apps/                   # Product feature modules
│   │   ├── account/
│   │   ├── blogs/
│   │   ├── commerce/
│   │   ├── document-library/
│   │   ├── journal/            # Web Content
│   │   ├── portal-search/
│   │   └── ...
│   ├── core/                   # Framework / platform modules
│   │   ├── petra/
│   │   ├── portal-bootstrap/
│   │   └── ...
│   ├── dxp/                    # DXP-only (enterprise) modules
│   ├── private/                # Private/EE modules (may be absent in CE)
│   └── test/                   # Test infrastructure
│
├── portal-impl/                # Core portal implementation (legacy + shared)
│   └── src/
│       ├── com/liferay/portal/ # Portal services, utilities, legacy portlets
│       └── portal.properties   # Master configuration defaults
│
├── portal-kernel/              # Public API surface (interfaces, base classes)
│   └── src/com/liferay/portal/kernel/
│
├── portal-web/                 # WAR: JSPs, themes, static resources
│   └── docroot/
│       ├── html/               # Legacy JSP portlets
│       ├── WEB-INF/
│       └── errors/
│
├── portal-service/             # (Older repos) or merged into portal-kernel
│
├── util-bridges/               # JSF, Struts, Spring bridge utilities
├── util-java/                  # General Java utilities
├── util-taglib/                # JSP tag libraries
│
├── themes/                     # Classic/styled/admin base themes
│
├── sql/                        # DB schema, indexes, sequences
│   ├── portal-tables.sql
│   ├── indexes.sql
│   └── create/
│
├── lib/                        # Third-party JARs (pre-OSGi dependencies)
│
├── tools/                      # Build tools, SDK, Ant tasks
│   └── sdk/
│
├── build.xml                   # Root Ant build
├── build-common.xml
├── gradlew / settings.gradle   # Gradle workspace entry points
└── .gradle/
```

---

## Module Structure (inside `modules/`)

Each module follows OSGi bundle conventions:

```
modules/apps/<product>/<bundle-name>/
├── bnd.bnd                        # Bundle symbolic name, version, exports
├── build.gradle                   # Dependencies, tasks
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/liferay/...   # Java source
│   │   └── resources/
│   │       ├── META-INF/
│   │       │   └── resources/     # JSP, CSS, JS for the module
│   │       └── content/           # i18n Language.properties
│   └── test/
│       └── java/                  # Unit + integration tests
└── package-info.java (optional)
```

Service Builder modules add:

```
├── <bundle>-api/          # Generated interfaces + model classes
├── <bundle>-service/      # Generated service implementation
│   └── service.xml        # Entity definitions → triggers code gen
└── <bundle>-web/          # Portlet frontend
```

---

## Key Patterns & How to Find Things

### Finding a class

```bash
# Fast: use find + grep
find "$LIFERAY_PORTAL" -name "ClassName.java" 2>/dev/null

# With partial name
find "$LIFERAY_PORTAL" -name "*Journal*Service*.java" 2>/dev/null
```

### Finding where a portlet lives

```bash
# By portlet name keyword
grep -r "com.liferay.portlet.display-name" "$LIFERAY_PORTAL/modules" \
  --include="*.properties" -l | grep -i "<keyword>"

# By portlet ID / javax.portlet.name
grep -r "javax.portlet.name=" "$LIFERAY_PORTAL/modules" \
  --include="*.java" -l | grep -i "<keyword>"
```

### Finding OSGi component registration

```bash
grep -r "@Component" "$LIFERAY_PORTAL/modules/apps/<product>" \
  --include="*.java" -l
```

### Finding Service Builder entities

```bash
find "$LIFERAY_PORTAL" -name "service.xml" | xargs grep -l "<entity name"
```

### Searching configuration properties

```bash
grep -r "some.config.key" "$LIFERAY_PORTAL/portal-impl/src/portal.properties"
grep -r "some.config.key" "$LIFERAY_PORTAL/modules" --include="*.cfg" -l
```

---

## Build System

Liferay uses **both Ant and Gradle** depending on location:

| Area | Build tool | Command |
|---|---|---|
| Root / portal-impl / portal-web | Ant | `ant -f build.xml <target>` |
| modules/ (OSGi bundles) | Gradle | `./gradlew :<module-path>:deploy` |
| Single module deploy | Gradle | `cd modules/apps/X/Y && ../../../gradlew deploy` |
| Build all modules | Gradle | `./gradlew deploy` (slow) |
| Run tests | Gradle | `./gradlew <module>:test` |
| Clean | Gradle | `./gradlew clean` |

Common Gradle tasks:
- `deploy` — build JAR and copy to Liferay's `osgi/modules/`
- `buildService` — regenerate Service Builder code from `service.xml`
- `formatSource` — run code formatter (required before commits)
- `jar` — build without deploying

---

## OSGi & Declarative Services (DS)

Liferay 7+ is OSGi-based. Key annotations:

```java
@Component(
    immediate = true,
    property = {
        "javax.portlet.name=" + MyPortletKeys.MY_PORTLET
    },
    service = Portlet.class
)
public class MyPortlet extends MVCPortlet { ... }
```

- Services are wired via `@Reference` injection
- Configuration uses `@Meta.OCD` + `@ExtendedObjectClassDefinition`
- Component factories use `@Component(factory = "...")`

When modifying a component, check `bnd.bnd` to confirm the package is exported if it's part of the API.

---

## Frontend (JS / CSS)

Modern Liferay frontend lives in:

```
modules/apps/<product>/<bundle>-web/src/main/resources/META-INF/resources/
├── js/           # ES modules, Clay components, React
├── css/          # SCSS
└── *.jsp         # Server-side templates
```

Older portlets use:
```
portal-web/docroot/html/portlet/<portlet-name>/
```

JS build output is managed by `liferay-npm-bundler` or Webpack; check `package.json` in the module.

---

## Database / SQL

Schema lives in:
```
sql/portal-tables.sql      # Table definitions
sql/indexes.sql            # Index definitions
sql/sequences.sql          # Sequences (Oracle / PostgreSQL)
sql/create/               # Per-database DDL
```

Service Builder auto-generates `*ModelImpl.java` mapped to tables. Column → field mappings are in `service.xml`.

---

## Common Tasks Cheat Sheet

| Task | Where to look |
|---|---|
| Add a new portlet | `modules/apps/<product>/` — create `-web` module with `@Component(service = Portlet.class)` |
| Override a service | Create a module with `@Component(service = XService.class)` with higher `service.ranking` |
| Add a new entity | Edit `service.xml` → run `buildService` |
| Change portal.properties default | `portal-impl/src/portal.properties` (dev) or `portal-ext.properties` (runtime) |
| Add language keys | `src/main/resources/content/Language.properties` in the relevant module |
| Customize a JSP | Use Dynamic Include or JSP hook via `CustomJspBag` implementation |
| Add a configuration UI | Implement `ConfigurationScreen` or use System Settings via `@Meta.OCD` |
| Check if an asset type has its own native "view" widget on a page (vs. needing a generic/embedded preview) | `AssetRendererFactory.getURLView(LiferayPortletResponse, WindowState)` — a generic, type-agnostic hook (unrelated to Objects specifically). `BaseAssetRendererFactory`'s default returns `null`; `DLFileEntry`/`DLFolder`/`JournalArticle`/`JournalFolder`/`BlogsEntry`/`WikiPage`/`MBMessage`/`MBCategory`/Bookmarks override it for real. Objects/KBArticle don't, so they fall through to an embedded preview. |

---

## Tips

- **Never edit generated files** — classes in `*-service/src/main/java/.../service/impl/` that are prefixed with `Base` are generated. Edit only `*LocalServiceImpl.java` / `*ServiceImpl.java`.
- **Check `bnd.bnd` versions** — bump `Bundle-Version` when modifying a module or the OSGi container won't pick up changes.
- **Gradle wrapper** — always use `./gradlew` (not system `gradle`) to respect the project's Gradle version.
- **Format before committing** — run `./gradlew formatSource` to avoid CI failures.
- **DXP vs CE** — modules under `modules/dxp/` or `modules/private/` are enterprise-only and may not be present in Community Edition checkouts.
- **`ThemeDisplay.getURLCurrent()` vs `request.getRequestURL()`** — the friendly URL filter rewrites a request like `/web/guest/object-list` to `/c/portal/layout?p_l_id=...` *before* the portlet sees it, so `getRequestURL()` always returns the rewritten form, not what the browser's address bar shows. Use `getURLCurrent()` when you need the actual friendly URL (e.g. to detect what page/widget the user is currently on).
