#!/usr/bin/env bash
# Reinicio de servicios en prod (ejecutar en el servidor con sudo si aplica).
# Uso: ./scripts/restart_prod_services.sh

set -e
echo "Reiniciando gunicorn..."
sudo systemctl restart gunicorn
echo "Reiniciando nginx..."
sudo systemctl restart nginx
echo "Listo."
