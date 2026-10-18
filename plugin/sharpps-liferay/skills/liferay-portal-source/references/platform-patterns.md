Build/deploy commands below describe the upstream tree, not permission to run them. Prefer a read-only source lookup; obtain authorization before deploying or changing a runtime.

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
