#!/usr/bin/env bash
# eGarage visual asset export pipeline
# Usage:
#   ./marketing/scripts/export_assets.sh            # export all masters
#   ./marketing/scripts/export_assets.sh --check    # status report only
#   ./marketing/scripts/export_assets.sh --dry-run  # preview without writing
#   ./marketing/scripts/export_assets.sh taller     # export one scene

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Locate Python (prefer project venv, fall back to system python3)
PYTHON=""
for candidate in \
    "$PROJECT_ROOT/.venv/bin/python3" \
    "$PROJECT_ROOT/venv/bin/python3" \
    "$(which python3 2>/dev/null)"; do
    if [[ -x "$candidate" ]]; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "ERROR: python3 not found. Activate your virtualenv and re-run." >&2
    exit 1
fi

"$PYTHON" "$SCRIPT_DIR/export_assets.py" "$@"
