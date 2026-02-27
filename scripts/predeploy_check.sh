#!/usr/bin/env bash
set -euo pipefail
cd /srv/egarage

echo "== Django check =="
./scripts/manage_prod.sh check

echo "== Pending migrations (plan) =="
PLAN="$(./scripts/manage_prod.sh migrate --plan || true)"
echo "$PLAN" | tail -n 80

# Si aparece cualquier línea tipo "taller.0081 ..." o "account.000X ..." -> hay pendientes
if echo "$PLAN" | grep -qE "^\s*[a-zA-Z0-9_]+\.\d+"; then
  echo "ERROR: There are unapplied migrations. Run ./scripts/manage_prod.sh migrate"
  exit 1
fi

echo "OK: predeploy checks passed"
