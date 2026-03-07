#!/bin/bash
# Fix 500 por og-br.png faltante en manifest de staticfiles
# Ejecutar en el servidor: bash scripts/fix_og_br_500.sh

set -e
PROJECT_DIR="${PROJECT_DIR:-/srv/egarage}"
ENV_PROD="${ENV_PROD:-$PROJECT_DIR/.env.prod}"

echo "=== Paso A: Crear og-br.png si no existe ==="
# static/ está en la raíz del proyecto (STATICFILES_DIRS)
sudo mkdir -p "$PROJECT_DIR/static/img"
if [ ! -f "$PROJECT_DIR/static/img/og-br.png" ]; then
  echo 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X8eQAAAABJRU5ErkJggg==' \
    | base64 -d | sudo tee "$PROJECT_DIR/static/img/og-br.png" >/dev/null
  sudo chown -R egarage:www-data "$PROJECT_DIR/static/img"
  sudo chmod 644 "$PROJECT_DIR/static/img/og-br.png"
  echo "  -> og-br.png creado"
else
  echo "  -> og-br.png ya existe"
fi

echo ""
echo "=== Paso B: collectstatic con .env.prod ==="
cd "$PROJECT_DIR"
source venv/bin/activate
set -a
source "${ENV_PROD}"
set +a
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn

echo ""
echo "=== Paso C: Verificar manifest ==="
ls -la "$PROJECT_DIR/staticfiles/staticfiles.json" 2>/dev/null || true
rg -n "img/og-br\.png" "$PROJECT_DIR/staticfiles/staticfiles.json" 2>/dev/null || echo "  (rg no disponible o no match)"

echo ""
echo "=== Paso D: Probar ==="
echo "  curl -I https://egarage.cl/br/pt/bienvenida/"
echo "  (Debe devolver 200, no 500)"
