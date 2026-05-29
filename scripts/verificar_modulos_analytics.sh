#!/bin/bash
# Script para verificar qué módulos de analytics están fallando
# Ejecutar en el servidor: sudo bash verificar_modulos_analytics.sh

set -e

echo "=========================================="
echo "🔍 Verificando módulos de analytics"
echo "=========================================="
echo ""

sudo -u egarage -H bash -lc '
cd /srv/egarage
/srv/egarage/venv/bin/python - <<PY
import importlib
import sys

mods = [
  "taller.analytics.views",
  "taller.analytics.admin_views",
  "taller.analytics.funcionalidades_adicionales",
  "taller.analytics.apis_avanzadas",
]

print("Verificando módulos de analytics...")
print("=" * 50)
print()

all_ok = True
for m in mods:
    try:
        importlib.import_module(m)
        print("✅ OK:", m)
    except ImportError as e:
        print("❌ FAIL (ImportError):", m)
        print("   =>", str(e))
        all_ok = False
    except SyntaxError as e:
        print("❌ FAIL (SyntaxError):", m)
        print("   =>", str(e))
        all_ok = False
    except Exception as e:
        print("❌ FAIL:", m)
        print("   =>", type(e).__name__ + ":", str(e))
        all_ok = False
    print()

if all_ok:
    print("=" * 50)
    print("✅ Todos los módulos se importaron correctamente")
    sys.exit(0)
else:
    print("=" * 50)
    print("❌ Algunos módulos fallaron al importar")
    sys.exit(1)
PY
'

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Verificación completada - Todos los módulos OK"
else
    echo "❌ Verificación completada - Hay módulos con errores"
fi
echo "=========================================="
