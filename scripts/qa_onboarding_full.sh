#!/bin/bash
set -u
set -o pipefail

HOST="${HOST:-www.egarage.cl}"
SESSION_INVALID="${SESSION_INVALID:-INVALID_SESSION}"
SESSION_VALID="${SESSION_VALID:-<SESSION_VALIDA>}"
ENDPOINT="${ENDPOINT:-https://127.0.0.1/cl/es/onboarding/identidad/}"
LOGFILE="${LOGFILE:-/srv/egarage/logs/qa_onboarding.log}"

LOG_ENABLED=1
if ! mkdir -p "$(dirname "$LOGFILE")" 2>/dev/null; then
  LOG_ENABLED=0
fi
if [ "$LOG_ENABLED" -eq 1 ] && ! touch "$LOGFILE" 2>/dev/null; then
  LOG_ENABLED=0
fi
if [ "$LOG_ENABLED" -ne 1 ]; then
  LOGFILE="/tmp/qa_onboarding.log"
  mkdir -p "$(dirname "$LOGFILE")" 2>/dev/null || true
  if touch "$LOGFILE" 2>/dev/null; then
    LOG_ENABLED=1
    echo "[WARN] No se pudo escribir en el log configurado. Usando fallback: $LOGFILE" 1>&2
  else
    LOG_ENABLED=0
    echo "[WARN] No se pudo escribir en ningun log (ni en el configurado ni en $LOGFILE). Logging solo por consola." 1>&2
  fi
fi

_ts() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  local msg="$*"
  if [ "$LOG_ENABLED" -eq 1 ]; then
    echo "[$(_ts)] $msg" | tee -a "$LOGFILE"
  else
    echo "[$(_ts)] $msg"
  fi
}

pass() {
  local msg="$*"
  log "PASS - $msg"
}

fail() {
  local msg="$*"
  log "FAIL - $msg"
  echo "ALERTA QA: $msg" 1>&2
  PASS_ALL=0
}

section() {
  log "--- $* ---"
}

PASS_ALL=1

log "=== QA PRODUCCIÓN ONBOARDING FULL AUTO ==="
log "HOST=$HOST"
log "ENDPOINT=$ENDPOINT"
log "LOGFILE=$LOGFILE"

if [ "$SESSION_VALID" = "<SESSION_VALIDA>" ] || [ -z "$SESSION_VALID" ]; then
  fail "SESSION_VALID no esta configurada (placeholder). Exporta SESSION_VALID con una cookie real: SESSION_VALID='...' ./qa_onboarding_full.sh"
fi

section "Verificando Gunicorn"
if systemctl is-active --quiet egarage-gunicorn 2>/dev/null; then
  pass "Servicio egarage-gunicorn activo"
elif systemctl is-active --quiet gunicorn 2>/dev/null; then
  pass "Servicio gunicorn activo"
else
  fail "Gunicorn no está activo (egarge-gunicorn/gunicorn)"
fi

section "Verificando Nginx (443)"
if ss -ltnp 2>/dev/null | grep -q ":443"; then
  pass "Puerto 443 en escucha"
else
  fail "No se detecta proceso escuchando en 443"
fi

section "Onboarding con sesión inválida (espera 302)"
STATUS_INVALID=$(curl -k -s -o /dev/null -w "%{http_code}" -H "Host: ${HOST}" -b "sessionid=${SESSION_INVALID}" "${ENDPOINT}" 2>/dev/null || echo "000")
log "HTTP status (invalid): $STATUS_INVALID"
if [ "$STATUS_INVALID" = "302" ]; then
  pass "Redirect 302 con sesión inválida"
else
  fail "Se esperaba 302 con sesión inválida, se obtuvo $STATUS_INVALID"
fi

section "Onboarding con sesión válida (espera 200)"
TMP_BODY="$(mktemp)"
TMP_HEADERS="$(mktemp)"
STATUS_VALID=$(curl -k -s -D "$TMP_HEADERS" -o "$TMP_BODY" -w "%{http_code}" -H "Host: ${HOST}" -b "sessionid=${SESSION_VALID}" "${ENDPOINT}" 2>/dev/null || echo "000")
log "HTTP status (valid): $STATUS_VALID"
if [ "$STATUS_VALID" = "200" ]; then
  pass "HTTP 200 con sesión válida"
else
  LOCATION=$(grep -i '^Location:' "$TMP_HEADERS" | head -n 1 | sed -e 's/\r$//' -e 's/^[Ll]ocation:[[:space:]]*//')
  if [ -n "${LOCATION:-}" ]; then
    log "Redirect Location: $LOCATION"
  fi
  log "Headers (valid) primeros 20:"
  if [ "$LOG_ENABLED" -eq 1 ]; then
    sed -n '1,20p' "$TMP_HEADERS" | sed 's/^/[HDR] /' | tee -a "$LOGFILE" >/dev/null
  else
    sed -n '1,20p' "$TMP_HEADERS" | sed 's/^/[HDR] /'
  fi
  fail "Se esperaba 200 con sesión válida, se obtuvo $STATUS_VALID"
fi

section "Validación de template (paso_identidad)"
if grep -q "paso_identidad" "$TMP_BODY"; then
  pass "Se detecta marcador 'paso_identidad' en HTML"
else
  fail "No se detecta 'paso_identidad' en HTML (posible template incorrecto o sesión no válida)"
fi

rm -f "$TMP_BODY" "$TMP_HEADERS" 2>/dev/null || true

section "RESULTADO FINAL"
if [ "$PASS_ALL" -eq 1 ]; then
  log "=== QA RESULT: PASS ==="
  exit 0
else
  log "=== QA RESULT: FAIL ==="
  log "Revisar logs en $LOGFILE"
  exit 1
fi
