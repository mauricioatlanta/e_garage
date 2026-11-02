#!/usr/bin/env bash
set -euo pipefail

BASE="https://www.egarage.cl"
PROJ="/srv/egarage"

echo "=== HEALTHCHECK eGarage ==="
echo "DATE_UTC=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "HOST=$(hostname)"

echo
echo "1) GUNICORN"
systemctl is-active gunicorn

echo
echo "2) TEMPLATE CRITICO"
test -f "$PROJ/templates/components/ayuda_contextual.html" && echo "OK template" || { echo "FAIL template"; exit 1; }
grep -q 'components/ayuda_contextual.html' "$PROJ/templates/base.html" && echo "OK include" || { echo "FAIL include"; exit 1; }

echo
echo "3) RUTAS USA OK"
for u in "$BASE/us/login/" "$BASE/us/signup/"; do
    code=$(curl -k -s -o /dev/null -w "%{http_code}" "$u")
    echo "$u -> $code"
    [ "$code" = "200" ] || { echo "FAIL $u"; exit 1; }
done

echo
echo "4) LEGACY BLOQUEADO"
for u in "$BASE/us/en/accounts/login/" "$BASE/us/en/accounts/signup/"; do
    code=$(curl -k -s -o /dev/null -w "%{http_code}" "$u")
    echo "$u -> $code"
    [ "$code" = "404" ] || { echo "FAIL legacy $u"; exit 1; }
done

echo
echo "5) ERRORES"
journalctl -u gunicorn -n 50 --no-pager | grep -Ei "error|exception|traceback" && { echo "FAIL errores"; exit 1; } || echo "OK sin errores"

echo
echo "=== PRODUCCION OK ==="
