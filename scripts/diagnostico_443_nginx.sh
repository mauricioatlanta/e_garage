#!/bin/bash
# Script de diagnóstico: quién atiende 443 y qué está enabled
# Ejecutar en el servidor: sudo bash diagnostico_443_nginx.sh
# Objetivo: descubrir si 00-default-redirect está "robando" el 443 de egarage

echo "=============================================="
echo "1) SITES ENABLED (qué vhosts están activos)"
echo "=============================================="
sudo ls -lah /etc/nginx/sites-enabled

echo ""
echo "=============================================="
echo "2) CONTENIDO 00-default-redirect (primeras 220 líneas)"
echo "=============================================="
sudo sed -n '1,220p' /etc/nginx/sites-available/00-default-redirect 2>/dev/null || echo "(archivo no encontrado)"

echo ""
echo "=============================================="
echo "3) CONTENIDO default (primeras 260 líneas)"
echo "=============================================="
sudo sed -n '1,260p' /etc/nginx/sites-available/default 2>/dev/null || echo "(archivo no encontrado)"

echo ""
echo "=============================================="
echo "4) SITE EGARAGE (si existe)"
echo "=============================================="
if [ -f /etc/nginx/sites-available/egarage ]; then
  sudo sed -n '1,300p' /etc/nginx/sites-available/egarage
elif [ -f /etc/nginx/sites-available/egarage.cl ]; then
  sudo sed -n '1,300p' /etc/nginx/sites-available/egarage.cl
else
  echo "No se encontró egarage ni egarage.cl en sites-available"
  echo "Archivos en sites-available:"
  sudo ls -la /etc/nginx/sites-available/
fi

echo ""
echo "=============================================="
echo "5) TEST curl HTTPS local (egarage.cl y www)"
echo "=============================================="
echo "--- egarage.cl:443 ---"
curl -kI "https://egarage.cl/us/settings/" --resolve "egarage.cl:443:127.0.0.1" 2>/dev/null || echo "curl falló"

echo ""
echo "--- www.egarage.cl:443 ---"
curl -kI "https://www.egarage.cl/us/settings/" --resolve "www.egarage.cl:443:127.0.0.1" 2>/dev/null || echo "curl falló"

echo ""
echo "=============================================="
echo "6) NGINX -t (validar config)"
echo "=============================================="
sudo nginx -t
