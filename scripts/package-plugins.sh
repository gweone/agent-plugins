#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugins_root="$repo_root/plugin"
artifacts_dir="$repo_root/artifacts"

command -v python3 >/dev/null 2>&1 || {
    echo "error: python3 is required" >&2
    exit 1
}
command -v zip >/dev/null 2>&1 || {
    echo "error: zip is required" >&2
    exit 1
}

mkdir -p "$artifacts_dir"
staging_dir="$(mktemp -d)"
trap 'rm -rf "$staging_dir"' EXIT

plugin_count=0
for plugin_dir in "$plugins_root"/*; do
    [[ -d "$plugin_dir/.codex-plugin" ]] || continue
    manifest="$plugin_dir/.codex-plugin/plugin.json"

    read -r plugin_name plugin_version < <(
        python3 - "$manifest" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    manifest = json.load(stream)

name = manifest.get("name")
version = manifest.get("version")
if not name or not version:
    raise SystemExit("manifest must contain name and version")
print(name, version)
PY
    )

    relative_plugin="${plugin_dir#"$repo_root/"}"
    package_root="$staging_dir/$plugin_name"
    mkdir -p "$staging_dir"
    cp -a "$plugin_dir" "$package_root"

    find "$package_root" -type d \( \
        -name '__pycache__' -o \
        -name '.pytest_cache' -o \
        -name '.mypy_cache' \
    \) -prune -exec rm -rf {} +
    find "$package_root" -type f \( \
        -name '*.pyc' -o \
        -name '.DS_Store' \
    \) -delete

    output="$artifacts_dir/${plugin_name}-${plugin_version}.zip"
    rm -f "$output"
    (
        cd "$staging_dir"
        zip -q -r "$output" "$plugin_name"
    )

    printf 'created %s from %s\n' "${output#"$repo_root/"}" "$relative_plugin"
    plugin_count=$((plugin_count + 1))
done

if [[ "$plugin_count" -eq 0 ]]; then
    echo "error: no plugin packages found under $plugins_root" >&2
    exit 1
fi

printf 'packaged %d plugin(s) into %s\n' "$plugin_count" "${artifacts_dir#"$repo_root/"}"
