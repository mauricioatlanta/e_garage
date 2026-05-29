#!/usr/bin/env bash
# DIAGNÓSTICO AVANZADO eGarage (Desktop + Mobile + Logs)
# Este script realiza pruebas reales de HTTP status simulando diferentes dispositivos
# y captura errores en el journal de Gunicorn en tiempo real.

set -euo pipefail

BASE="https://www.egarage.cl"
UA_IPHONE="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")

echo "=== DIAGNÓSTICO AVANZADO eGarage ==="
echo "INICIO: $START_TIME"
echo "URL BASE: $BASE"
echo

test_url() {
    local url=$1
    local name=$2
    local ua=${3:-"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/100.0.0.0 Safari/537.36"}
    local device=${4:-"DESKTOP"}

    echo -n "probando $name ($device) -> "
    code=$(curl -k -s -L -o /dev/null -w "%{http_code}" -A "$ua" "$url")
    
    if [ "$code" = "200" ]; then
        echo "✅ $code OK"
    else
        echo "❌ $code FALLO"
        return 1
    fi
}

# 1) PRUEBAS DE ENDPOINTS CRÍTICOS
ERRORS=0

echo "--- 1) PRUEBAS HTTP ---"
# USA LOGIN
test_url "$BASE/us/login/" "USA LOGIN" || ERRORS=$((ERRORS+1))
test_url "$BASE/us/login/" "USA LOGIN" "$UA_IPHONE" "MOBILE" || ERRORS=$((ERRORS+1))

# USA SIGNUP
test_url "$BASE/us/signup/" "USA SIGNUP" || ERRORS=$((ERRORS+1))
test_url "$BASE/us/signup/" "USA SIGNUP" "$UA_IPHONE" "MOBILE" || ERRORS=$((ERRORS+1))

# CHILE HOME
test_url "$BASE/cl/es/" "CHILE HOME" || ERRORS=$((ERRORS+1))
test_url "$BASE/cl/es/" "CHILE HOME" "$UA_IPHONE" "MOBILE" || ERRORS=$((ERRORS+1))

echo
echo "--- 2) INSPECCIÓN DE LOGS (Desde el inicio del script) ---"
# Buscamos errores que hayan ocurrido durante la ejecución de este script
log_errors=$(journalctl -u gunicorn --since "$START_TIME" --no-pager | grep -Ei "error|exception|traceback" || true)

if [ -n "$log_errors" ]; then
    echo "⚠️ SE DETECTARON ERRORES EN LOS LOGS DURANTE LAS PRUEBAS:"
    echo "$log_errors"
    ERRORS=$((ERRORS+1))
else
    echo "✅ No se detectaron excepciones en Gunicorn durante las pruebas."
fi

echo
echo "=== RESULTADO FINAL ==="
if [ $ERRORS -eq 0 ]; then
    echo "🚀 SISTEMA 100% OPERATIVO (Desktop & Mobile)"
    exit 0
else
    echo "🚨 SE DETECTARON $ERRORS FALLOS. REVISAR LOGS."
    exit 1
fi
