#!/bin/bash
# Verificar que los templates de bienvenida están actualizados en el servidor
# Ejecutar EN EL SERVIDOR: cd /srv/egarage && bash scripts/verificar_bienvenida_templates_servidor.sh

set -e
cd "$(dirname "$0")/.."
BASE="${PWD}"

echo "=============================================="
echo "  Verificación templates bienvenida (servidor)"
echo "=============================================="
echo ""

# Activar venv si existe
if [ -d "venv/bin" ]; then
  source venv/bin/activate
fi

echo "[1] Archivos de templates en disco"
echo "-----------------------------------"
for rel in ar/es/onboarding/bienvenida.html \
           cl/es/onboarding/bienvenida.html \
           co/es/onboarding/bienvenida.html \
           us/es/onboarding/bienvenida.html \
           us/en/onboarding/bienvenida.html \
           mx/es/onboarding/bienvenida.html \
           ec/es/onboarding/bienvenida.html \
           uy/es/onboarding/bienvenida.html; do
  f="${BASE}/templates/${rel}"
  if [ -f "$f" ]; then
    mod=$(stat -c %y "$f" 2>/dev/null | cut -d' ' -f1) || mod="?"
    if grep -q "futuristic-glow\|glass-card" "$f" 2>/dev/null; then
      echo "  OK  $rel (refactor, mod: $mod)"
    else
      echo "  ??  $rel (existe pero sin firma refactor, mod: $mod)"
    fi
  else
    echo "  NO  $rel"
  fi
done

echo ""
echo "[2] Django: rutas de TEMPLATES y existencia"
echo "---------------------------------------------"
python -c "
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
import django
django.setup()
from pathlib import Path
from django.conf import settings
base = Path(settings.BASE_DIR)
tdirs = settings.TEMPLATES[0].get('DIRS', [])
print('  TEMPLATES DIRS:', tdirs)
for d in tdirs:
    p = Path(d)
    if not p.is_absolute():
        p = base / p
    ar = p / 'ar' / 'es' / 'onboarding' / 'bienvenida.html'
    print('  ar bienvenida exists:', ar.exists())
    break
" 2>/dev/null || echo "  (No se pudo ejecutar Django)"

echo ""
echo "[3] Servicio Gunicorn"
echo "---------------------"
if systemctl is-active --quiet egarage-gunicorn 2>/dev/null; then
  echo "  egarage-gunicorn: activo"
elif systemctl is-active --quiet gunicorn 2>/dev/null; then
  echo "  gunicorn: activo"
else
  echo "  No se detectó egarage-gunicorn ni gunicorn activo."
fi

echo ""
echo "=============================================="
echo "  Acciones recomendadas"
echo "=============================================="
echo "  1. Si algún template marca ?? o NO: desplegar de nuevo templates/"
echo "  2. Reiniciar app: sudo systemctl restart egarage-gunicorn"
echo "  3. Si usas Cloudflare: purgar caché (Caching → Purge Cache)"
echo "  4. En el navegador: Ctrl+Shift+R o probar en incógnito"
echo ""
