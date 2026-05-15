#!/usr/bin/env bash
#
# Fija DJANGO_ALLOWED_HOSTS en .env.prod para incluir la IP del servidor (159.223.200.106).
# Así se evita DisallowedHost cuando se accede por IP.
#
# Uso en el servidor:
#   cd /srv/egarage
#   bash scripts/root_scripts/fix_allowed_hosts_env_prod.sh
#
# Si ves errores raros (-H: command not found, SyntaxError en Python): el archivo puede tener
# finales de línea CRLF. Normalizar con: sed -i 's/\r$//' scripts/root_scripts/fix_allowed_hosts_env_prod.sh
#
# Requiere: .env.prod en EGARAGE_ROOT (por defecto /srv/egarage).
set -e

EGARAGE_ROOT="${EGARAGE_ROOT:-/srv/egarage}"
ENV_PROD="${EGARAGE_ROOT}/.env.prod"
REQUIRED_HOSTS="localhost,127.0.0.1,egarage.cl,www.egarage.cl,159.223.200.106"

if [[ ! -f "$ENV_PROD" ]]; then
  echo "ERROR: No existe $ENV_PROD (EGARAGE_ROOT=$EGARAGE_ROOT)"
  exit 1
fi

printf '\n===== BACKUP .env.prod =====\n'
cp "$ENV_PROD" "${ENV_PROD}.bak.$(date +%F-%H%M%S)"

printf '\n===== FIJAR DJANGO_ALLOWED_HOSTS EN .env.prod =====\n'
python3 - "$ENV_PROD" "$REQUIRED_HOSTS" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
value_line = f"DJANGO_ALLOWED_HOSTS={sys.argv[2]}"
target = "DJANGO_ALLOWED_HOSTS="

text = path.read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()
out = []
replaced = False

for line in lines:
    if line.strip().startswith(target):
        out.append(value_line)
        replaced = True
    else:
        out.append(line)

if not replaced:
    out.append(value_line)

path.write_text("\n".join(out) + "\n", encoding="utf-8")
print("OK_ENV_UPDATED")
PY

printf '\n===== CONFIRMAR CAMBIO =====\n'
grep -n '^DJANGO_ALLOWED_HOSTS=' "$ENV_PROD" || true

printf '\n===== REINICIAR GUNICORN =====\n'
sudo systemctl restart gunicorn
sudo systemctl status gunicorn --no-pager -l

printf '\n===== PROBAR IP DIRECTA =====\n'
curl -kI https://159.223.200.106/ -H 'Host: 159.223.200.106' || true

printf '\n===== ULTIMOS LOGS GUNICORN =====\n'
sudo journalctl -u gunicorn -n 40 --no-pager
