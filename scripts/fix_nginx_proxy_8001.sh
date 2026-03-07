#!/usr/bin/env bash
# Fix Nginx: reemplazar proxy al socket por 127.0.0.1:8001 y asegurar X-Forwarded-Proto.
# EJECUTAR EN EL SERVIDOR (donde está Nginx), con la ruta correcta del vhost.
#
# Uso:
#   sudo bash fix_nginx_proxy_8001.sh
#   # o indicando el archivo del vhost:
#   sudo bash fix_nginx_proxy_8001.sh /etc/nginx/sites-enabled/egarage

set -e

VHOST="${1:-/etc/nginx/sites-enabled/egarage}"

if [[ ! -f "$VHOST" ]]; then
  echo "No existe: $VHOST"
  echo "Uso: sudo bash fix_nginx_proxy_8001.sh [ruta_al_vhost]"
  echo "Ejemplo: sudo bash fix_nginx_proxy_8001.sh /etc/nginx/sites-enabled/egarage.cl"
  exit 1
fi

# Backup
cp -a "$VHOST" "${VHOST}.bak.$(date +%Y%m%d%H%M%S)"

# Reemplazar socket por puerto 8001
sed -i 's|proxy_pass http://unix:/run/gunicorn/gunicorn.sock;|proxy_pass http://127.0.0.1:8001;|g' "$VHOST"

# Añadir X-Forwarded-Proto si no está (después de X-Forwarded-For en el mismo location /)
if ! grep -q 'X-Forwarded-Proto' "$VHOST"; then
  sed -i '/proxy_set_header X-Forwarded-For/a\    proxy_set_header X-Forwarded-Proto \$scheme;' "$VHOST"
fi

echo "Config aplicada en $VHOST. Comprobando Nginx..."
nginx -t

echo "Recargando Nginx..."
systemctl reload nginx

echo "Listo. Verifica con: curl -I http://127.0.0.1/ -H 'Host: egarage.cl'"
