#!/usr/bin/env bash
set -e

cd /srv/egarage

echo "=== ROLLBACK ==="

git log --oneline -n 5

echo "👉 pega commit a volver:"
read commit

git reset --hard "$commit"

source venv/bin/activate
python manage.py migrate --noinput

systemctl restart gunicorn

echo "=== ROLLBACK OK ==="
