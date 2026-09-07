#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/.agents/skills"
CHECK_ONLY=false

if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=true
fi

mkdir -p "$DEST"

count=0
while IFS= read -r -d '' skill; do
  name="$(basename "$skill")"
  target="$DEST/$name"
  expected="$(realpath --relative-to="$DEST" "$skill")"
  count=$((count + 1))

  if [[ "$CHECK_ONLY" == true ]]; then
    [[ -L "$target" ]] || { echo "MISSING LINK: $target"; exit 1; }
    [[ "$(readlink "$target")" == "$expected" ]] || { echo "BAD LINK: $target -> $(readlink "$target")"; exit 1; }
    [[ -f "$target/SKILL.md" ]] || { echo "MISSING SKILL.md: $target"; exit 1; }
  else
    rm -rf "$target"
    ln -s "$expected" "$target"
  fi

done < <(find "$ROOT/plugins" -mindepth 3 -maxdepth 3 -type d -path '*/skills/*' -print0 | sort -z)

# Validate frontmatter in every exposed skill.
while IFS= read -r -d '' skill_md; do
  first="$(sed -n '1p' "$skill_md")"
  second="$(sed -n '2p' "$skill_md")"
  third="$(sed -n '3p' "$skill_md")"
  [[ "$first" == "---" ]] || { echo "INVALID FRONTMATTER: $skill_md"; exit 1; }
  grep -q '^name:' "$skill_md" || { echo "MISSING name: $skill_md"; exit 1; }
  grep -q '^description:' "$skill_md" || { echo "MISSING description: $skill_md"; exit 1; }
done < <(find "$DEST" -mindepth 2 -maxdepth 2 -type f -name SKILL.md -print0 | sort -z)

echo "Agent skills: $count canonical skills exposed via $DEST"
