#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/srv/egarage"
BRANCH="${1:-prod-good-cache-servicios-20260429}"
HOST_HEADER="www.egarage.cl"
SOCKET="/run/gunicorn/gunicorn.sock"

cd "$APP_DIR"
source venv/bin/activate

PREV_COMMIT="$(git rev-parse HEAD)"
echo "PREV_COMMIT=$PREV_COMMIT"

rollback() {
  echo "DEPLOY FAILED - ROLLBACK"
  git reset --hard "$PREV_COMMIT"
  sudo systemctl restart gunicorn
  sudo systemctl restart nginx
  exit 1
}
trap rollback ERR

echo "===== FETCH ====="
git fetch origin

echo "===== CHECKOUT BRANCH ====="
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "===== VALIDACIONES ====="
python manage.py check
python - <<'PY2'
import py_compile
import subprocess
import sys
from pathlib import Path

files = subprocess.check_output(["git", "ls-files", "*.py"], text=True).splitlines()
bad = []
for name in files:
    p = Path(name)
    if not p.exists():
        continue
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        bad.append((name, str(e)))

if bad:
    print("PY_COMPILE_FAILED")
    for name, err in bad[:30]:
        print(name, err)
    sys.exit(1)

print(f"PY_COMPILE_OK {len(files)} files")
PY2

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

echo "===== HEALTH CHECK ====="
curl --fail --max-time 10 --unix-socket "$SOCKET"   -H "Host: $HOST_HEADER"   -H "X-Forwarded-Proto: https"   http://localhost/healthz/

echo "===== SMOKE TEST SERVICIOS ====="
curl --fail --max-time 15 --unix-socket "$SOCKET"   -H "Host: $HOST_HEADER"   -H "X-Forwarded-Proto: https"   -o /dev/null   http://localhost/cl/es/servicios/api/menu/

echo "===== OK DEPLOY ====="
git log --oneline -1
