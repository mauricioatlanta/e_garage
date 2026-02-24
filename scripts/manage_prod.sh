#!/usr/bin/env bash
# Wrapper para ejecutar manage.py con settings_prod y el mismo .env que producción.
# Uso: ./scripts/manage_prod.sh shell -c "..."  |  ./scripts/manage_prod.sh check --deploy
set -euo pipefail

# Raíz del proyecto (donde está manage.py)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_PROD_FILE:-$ROOT/.env.prod}"
VENV_PYTHON="${VENV_PYTHON:-$ROOT/venv/bin/python}"
MANAGE="$ROOT/manage.py"

if [[ ! -f "$MANAGE" ]]; then
  echo "No se encontró manage.py en $ROOT" >&2
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "Aviso: no existe $ENV_FILE (variables de prod no cargadas)" >&2
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-gestion_taller.settings_prod}"
exec "$VENV_PYTHON" "$MANAGE" "$@"
