#!/usr/bin/env bash
# sync_bundle.sh
# Regenerate the assets bundled inside the aiws_cli package from the repository's
# canonical tool folders. Run this whenever the built-in skills or instruction
# files change so `aiws init` ships the latest content offline.
#
# Usage: bash cli/scripts/sync_bundle.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUNDLE="$SCRIPT_DIR/../src/aiws_cli/bundle"

# tool-key | instruction source (relative to repo root) | skills source dir
map=(
  "claude|CLAUDE.md|.claude/skills"
  "copilot|.github/copilot-instructions.md|.github/skills"
  "codex|AGENTS.md|.codex/skills"
)

echo "Rebuilding bundle at: $BUNDLE"
rm -rf "$BUNDLE"
mkdir -p "$BUNDLE"

for entry in "${map[@]}"; do
  IFS='|' read -r key inst skills <<< "$entry"
  dest="$BUNDLE/$key"
  mkdir -p "$dest/skills"
  cp "$REPO_ROOT/$inst" "$dest/$(basename "$inst")"
  cp -r "$REPO_ROOT/$skills/." "$dest/skills/"
  n=$(find "$dest/skills" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')
  echo "  $key: $(basename "$inst") + $n skill(s)"
done

echo "Bundle rebuilt."

