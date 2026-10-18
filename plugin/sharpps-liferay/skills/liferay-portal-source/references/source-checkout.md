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

Before relying on a resolved source tree, run a quick orientation if you have not already:

```bash
# Top-level structure
ls "$LIFERAY_PORTAL"

# Identify the version
cat "$LIFERAY_PORTAL/release.properties" 2>/dev/null \
  || cat "$LIFERAY_PORTAL/portal-impl/src/portal.properties" 2>/dev/null | grep "^build.number" \
  || git -C "$LIFERAY_PORTAL" log --oneline -1
```

Do NOT skip orientation — the layout differs between Liferay 7.0, 7.1, 7.2, 7.3, 7.4, and DXP versions.
