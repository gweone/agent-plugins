# Tokens and source verification

> Source paths (`modules/...`, `workspaces/...`, `$LIFERAY_PORTAL/...`) refer to an external Liferay Portal checkout, not files in this plugin repository. Resolve it with [liferay-portal-source](../../liferay-portal-source/SKILL.md). Consuming-workspace paths and project rules are illustrative precedents, not plugin-repository files or universal requirements.

## Token substitution (`[$TOKEN$]` / `"[#TOKEN#]"` inside any JSON/XML resource)

Confirmed by reading `SiteInitializerUtil` + the `stringUtilReplaceValues.put(...)` calls in
`BundleSiteInitializer` — **grep, don't guess**, since new tokens get added between releases:

```bash
grep -n 'stringUtilReplaceValues.put(' \
  modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/src/main/java/com/liferay/site/initializer/extender/internal/BundleSiteInitializer.java
```

Confirmed tokens as of this check:

| Token | Resolves to |
|---|---|
| `[$GROUP_ID$]`, `[$GROUP_KEY$]`, `[$COMPANY_ID$]`, `[$GROUP_FRIENDLY_URL$]`, `[$PORTAL_URL$]` | The target site's identifiers |
| `[$PORTAL_PROPERTY:<key>$]` | A whitelisted `portal.properties` value (small fixed whitelist — `default.guest.public.layout.*` keys) |
| `[$CLASS_NAME_ID:<fully.qualified.ClassName>$]` | classNameId, for a small fixed set of classes (Blogs/Calendar/DDL/DDM/DLFileEntry/DLFolder/Journal/KBArticle/MBMessage/WikiPage) |
| `[$DOCUMENT_URL:<resourcePath>$]`, `[$DOCUMENT_FILE_ENTRY_ID:<resourcePath>$]`, `[$DOCUMENT_JSON:<resourcePath>$]` | The just-imported document at that exact `site-initializer/...` resource path |
| `[$OBJECT_DEFINITION_CLASS_NAME:<ObjectName>$]`, `[$OBJECT_DEFINITION_ID:<ObjectName>$]`, `[$OBJECT_DEFINITION_PORTLET_ID:<ObjectName>$]` | Resolved from the `name` in `object-definitions/*.json` |
| `[$<ObjectShortName>#<externalReferenceCode>$]` | A specific Object Entry's numeric ID |
| `[$LAYOUT_ID:<Layout Name>$]` | A layout's ID, by its `name_i18n`/`name` |
| `[$DDM_STRUCTURE_ID:<structureKey>$]`, `[$DDM_TEMPLATE_ID:<templateName>$]`, `[$TEMPLATE_ENTRY_ID:<name>$]` | DDM structure/template IDs |
| `[$JOURNAL_ARTICLE_ID:<articleId>$]` | A Journal Article's resource primary key |
| `[$ASSET_LIST_ENTRY_ID:<key>$]`, `[$DOCUMENT_FILE_ENTRY_TYPE_ID:<key>$]` | Asset Publisher list / D&M file-entry-type IDs |
| `[$RELEASE_INFO:<field>$]` | Build/version metadata (`BUILD_NUMBER`, `VERSION`, ...) |

Tokens only resolve if the resource they reference **already ran** in the dependency graph —
e.g. don't reference `[$OBJECT_DEFINITION_CLASS_NAME:X$]` from `sxp-blueprints.json`; that step
has no declared dependency on object definitions, so it can execute first and leave the literal
text unreplaced. When unsure of execution order, check `_createRMap()`'s `_dependsOn(...)` lists
for both resources, or just test it.

## Verifying before claiming a resource type is/isn't supported

Don't answer "site initializers can't import X" from memory — grep the engine and the real
workspace samples first:

```bash
# Full list of resource "steps" the engine knows about, by name:
grep -oP '(?<=R\(\n?\s*")\w+(?=",)' \
  modules/apps/site-initializer/site-initializer-extender/site-initializer-extender/src/main/java/com/liferay/site/initializer/extender/internal/BundleSiteInitializer.java

# A concrete, exhaustive worked example with every resource type (used in Liferay's own
# integration tests for this exact engine — the most authoritative fixture available):
ls modules/apps/site-initializer/site-initializer-extender/site-initializer-extender-test-bundle-1/src/main/resources/site-initializer/

# Real production Client Extension site initializers, for client-extension.yaml conventions
# and to see which resource combinations actually ship together:
ls workspaces/*/client-extensions/*site-initializer*/site-initializer/
```

(All paths above are relative to the `liferay-portal` checkout, not this workspace.)
