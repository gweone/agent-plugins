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
