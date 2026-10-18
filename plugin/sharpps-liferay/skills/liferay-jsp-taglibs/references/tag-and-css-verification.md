Resolve `$LIFERAY_PORTAL` using [source navigation](../../liferay-portal-source/SKILL.md) before running source lookups. Examples must match the target version.

Prefer an existing supported tag/macro over equivalent hand-written HTML,
but verify availability and deprecation first. Do not invent `clay:modal`
or `<@clay.modal>`; use the appropriate React component or verified Clay
markup when no supported server-side tag covers the need.

For FTL, bridge JSP tags sparingly: a deprecated or lifecycle-dependent tag
is not automatically a good choice simply because it can be bridged.

## 3. Verifying before using

Don't guess a tag, macro, or CSS class exists — verify it:

```bash
# Does this JSP tag exist, and what attributes does it take?
grep -A 20 "<name>TAGNAME</name>" "$LIFERAY_PORTAL"/util-taglib/src/META-INF/liferay-*.tld

# Is this tag deprecated? Check its backing class.
find "$LIFERAY_PORTAL" -iname "*TagNameTag.java" -path "*aui*"

# Does this Clay FTL macro exist?
grep -n "<name>" "$LIFERAY_PORTAL/modules/apps/frontend-taglib/frontend-taglib-clay/src/main/resources/META-INF/liferay-clay.tld"

# Does the THEME actually ship the CSS class you're about to rely on?
# (Pull the live compiled clay.css and grep it — don't assume a class exists just
# because it's a "standard" Bootstrap/Clay name.)
curl -s "https://<host>/o/<theme-id>/css/clay.(<hash>).css" -o /tmp/clay.css
grep -o '\.classname{[^}]*}' /tmp/clay.css
```

This last technique — fetching the live theme's compiled CSS — is the most reliable way to
confirm a class/utility actually exists with the values you expect, rather than assuming the
SCSS source in `liferay-portal` matches what's deployed (theme overrides, build-time variable
maps, and Atlas/Cadmin variants can change the compiled output).

### Known Clay CSS gotchas (confirmed via live `clay.css`, not SCSS source)

- **`.label-item{display:flex;flex-direction:column}`** — a Clay label's inner content wrapper
  (the element you pass `innerElementProps`/`className` into on `Toolbar.Label`/`ClayLabel`)
  defaults to a *column* flex direction. Bootstrap's `d-inline-flex` only sets `display`, not
  `flex-direction`, so adding it alone still leaves icon+text stacked vertically — you also need
  `flex-row` explicitly.
- **`.dropdown-item-indicator-start{position:absolute}`** — a `ClayDropDown.Item`'s left-side
  icon/symbol is absolutely positioned and needs its *ancestor* dropdown menu to carry
  `.dropdown-menu-indicator-start` for the padding compensation that keeps it from overlapping
  the label text. `ClayDropDownWithItems` applies that ancestor class automatically; the
  lower-level `ClayDropDown` composition (menu built by hand from `ClayDropDown.Item`s) does not
  — pass `hasLeftSymbols` to `ClayDropDown` to get it, rather than trying to add the class
  manually (it has to land on the right ancestor, not the item itself).
