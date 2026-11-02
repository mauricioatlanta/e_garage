#!/usr/bin/env bash
set -e

cd /srv/egarage

echo "=== DEPLOY eGarage ==="

echo "1) GIT PULL"
git pull

echo "2) VENV"
source venv/bin/activate

echo "3) MIGRATIONS"
python manage.py migrate --noinput

echo "4) STATIC"
python manage.py collectstatic --noinput

echo "5) RESTART"
systemctl restart gunicorn
sleep 2

echo "6) HEALTHCHECK"
bash /srv/egarage/scripts/prod_healthcheck.sh

echo "=== DEPLOY OK ==="
