#!/usr/bin/env bash
# release.sh
# Build and (optionally) publish the aiws CLI to PyPI (Option C: wheel release).
#
# Steps performed:
#   1. Regenerate the offline asset bundle from the repo's canonical tool folders.
#   2. Clean previous build artifacts.
#   3. Build the wheel + sdist.
#   4. Verify the wheel actually contains the bundled assets (all 3 tools).
#   5. Optionally upload to PyPI (or TestPyPI) with twine.
#
# Usage:
#   bash cli/scripts/release.sh                 # build + verify only (no upload)
#   bash cli/scripts/release.sh --publish       # build, verify, upload to PyPI
#   bash cli/scripts/release.sh --publish-test  # build, verify, upload to TestPyPI
#
# Requirements: python3 with the 'build' and (for uploads) 'twine' packages.
#   pip install build twine
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve a Python launcher: prefer python3/python, fall back to the Windows 'py'.
# Note: on Windows a non-functional Store alias named 'python' may be on PATH, so
# each candidate is verified by actually executing it — not just command -v.
PY=""
for cand in python3 python py; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import sys" >/dev/null 2>&1; then
    PY="$cand"; break
  fi
done
if [[ -z "$PY" ]]; then
  echo "ERROR: no working Python interpreter found (tried python3, python, py)." >&2
  exit 1
fi
echo "Using Python: $PY"

PUBLISH="none"
case "${1:-}" in
  --publish) PUBLISH="pypi" ;;
  --publish-test) PUBLISH="testpypi" ;;
  "") PUBLISH="none" ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac

echo "==> 1/4  Regenerating offline asset bundle"
bash "$SCRIPT_DIR/sync_bundle.sh"

echo "==> 2/4  Cleaning previous build artifacts"
rm -rf "$CLI_DIR/dist" "$CLI_DIR/build" "$CLI_DIR"/src/*.egg-info

echo "==> 3/4  Building wheel + sdist"
( cd "$CLI_DIR" && "$PY" -m build )

echo "==> 4/4  Verifying the wheel contains the bundled assets"
WHEEL="$(ls -1 "$CLI_DIR"/dist/*.whl | head -n1)"
if [[ -z "$WHEEL" ]]; then
  echo "ERROR: no wheel produced in dist/." >&2
  exit 1
fi
echo "  Wheel: $(basename "$WHEEL")"

# Count bundled SKILL.md files inside the wheel (a .whl is a zip archive).
BUNDLED=$("$PY" - "$WHEEL" <<'PY'
import sys, zipfile
whl = sys.argv[1]
with zipfile.ZipFile(whl) as z:
    names = z.namelist()
skills = [n for n in names if "/bundle/" in n and n.endswith("SKILL.md")]
tools = {n.split("/bundle/")[1].split("/")[0] for n in names if "/bundle/" in n}
print(len(skills), ",".join(sorted(tools)))
PY
)
COUNT="${BUNDLED%% *}"
TOOLS="${BUNDLED#* }"
echo "  Bundled SKILL.md files: $COUNT   tools: $TOOLS"
if [[ "$COUNT" -lt 30 ]]; then
  echo "ERROR: wheel is missing bundled skills (expected 30+, got $COUNT)." >&2
  echo "       Did sync_bundle.sh run? Is 'artifacts' set in pyproject.toml?" >&2
  exit 1
fi
echo "  OK: bundle is present in the wheel."

case "$PUBLISH" in
  none)
    echo
    echo "Build complete. Artifacts in: $CLI_DIR/dist"
    echo "To publish:  bash cli/scripts/release.sh --publish       (PyPI)"
    echo "             bash cli/scripts/release.sh --publish-test  (TestPyPI)"
    ;;
  pypi)
    echo "==> Uploading to PyPI"
    ( cd "$CLI_DIR" && "$PY" -m twine upload dist/* )
    ;;
  testpypi)
    echo "==> Uploading to TestPyPI"
    ( cd "$CLI_DIR" && "$PY" -m twine upload --repository testpypi dist/* )
    ;;
esac

echo "Done."





