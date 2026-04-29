#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/srv/egarage"
BRANCH="${1:-prod-good-cache-servicios-20260429}"
HOST_HEADER="www.egarage.cl"
SOCKET="/run/gunicorn/gunicorn.sock"

cd "$APP_DIR"
source venv/bin/activate

echo "===== BACKUP PRE-DEPLOY ====="
PREV_COMMIT="$(git rev-parse HEAD)"
echo "PREV_COMMIT=$PREV_COMMIT"

echo "===== FETCH ====="
git fetch origin

echo "===== CHECKOUT BRANCH ====="
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "===== VALIDACIONES ====="
python manage.py check
python -m py_compile $(git ls-files "*.py")

echo "===== MIGRACIONES ====="
python manage.py migrate --noinput

echo "===== STATIC ====="
python manage.py collectstatic --noinput

echo "===== RESTART LIMPIO ====="
sudo systemctl stop gunicorn || true
pkill -9 gunicorn || true
sleep 2
sudo systemctl start gunicorn
sudo systemctl restart nginx
sudo systemctl start gunicorn
sudo systemctl restart nginx

echo "===== HEALTH CHECK ====="
curl --fail --max-time 10 --unix-socket "$SOCKET" \
  -H "Host: $HOST_HEADER" \
  -H "X-Forwarded-Proto: https" \
  http://localhost/healthz/

echo "===== SMOKE TEST SERVICIOS ====="
curl --fail --max-time 15 --unix-socket "$SOCKET" \
  -H "Host: $HOST_HEADER" \
  -H "X-Forwarded-Proto: https" \
  -o /dev/null \
  http://localhost/cl/es/servicios/api/menu/

echo "===== OK DEPLOY ====="
git log --oneline -1
