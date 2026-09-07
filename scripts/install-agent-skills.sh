#!/usr/bin/env bash
set -euo pipefail

# Validate canonical skills under ./plugin/*/skills only.
# Multi-agent hosts must reference each plugin package (./plugin/<name>) with skills: "./skills/".
# Do NOT treat .agents/skills as a skill root.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_ROOT="$ROOT/plugin"

if [[ ! -d "$PLUGIN_ROOT" ]]; then
  echo "MISSING: $PLUGIN_ROOT (expected canonical plugin packages here)"
  exit 1
fi

count=0
while IFS= read -r -d '' skill_md; do
  count=$((count + 1))
  first="$(sed -n '1p' "$skill_md")"
  [[ "$first" == "---" ]] || { echo "INVALID FRONTMATTER: $skill_md"; exit 1; }
  grep -q '^name:' "$skill_md" || { echo "MISSING name: $skill_md"; exit 1; }
  grep -q '^description:' "$skill_md" || { echo "MISSING description: $skill_md"; exit 1; }
done < <(find "$PLUGIN_ROOT" -mindepth 3 -maxdepth 4 -type f -path '*/skills/*/SKILL.md' -print0 | sort -z)

echo "OK: $count canonical skills under $PLUGIN_ROOT/*/skills/"
echo "Hosts should load skills via ./plugin/<name> + skills path ./skills/"
