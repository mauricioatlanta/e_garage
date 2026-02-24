#!/bin/bash
# Script completo para corregir y agregar stubs a taller/analytics/views.py
# Ejecutar en el servidor: sudo bash fix_analytics_views_completo.sh

set -e

VIEWS_FILE="/srv/egarage/taller/analytics/views.py"
BACKUP_FILE="/srv/egarage/taller/analytics/views.py.backup.$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$VIEWS_FILE" ]; then
    echo "❌ Error: No se encontró $VIEWS_FILE"
    exit 1
fi

echo "=========================================="
echo "🔧 Corrigiendo analytics/views.py"
echo "=========================================="
echo ""

# 1. Hacer backup
echo "[1] Creando backup..."
cp "$VIEWS_FILE" "$BACKUP_FILE"
echo "✅ Backup creado: $BACKUP_FILE"
echo ""

# 2. Limpiar stubs anteriores si existen
echo "[2] Limpiando stubs anteriores..."
if grep -q "# --- HOTFIX: stubs para compatibilidad con urls.py ---" "$VIEWS_FILE"; then
    # Eliminar desde el comentario HOTFIX hasta el final
    sed -i '/# --- HOTFIX: stubs para compatibilidad con urls.py ---/,$d' "$VIEWS_FILE"
    echo "✅ Stubs anteriores eliminados"
else
    echo "ℹ️  No se encontraron stubs anteriores"
fi
echo ""

# 3. Verificar que el archivo termina correctamente
echo "[3] Verificando final del archivo..."
# Eliminar líneas vacías al final
sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$VIEWS_FILE" 2>/dev/null || true
# Asegurar que termina con salto de línea
if [ -s "$VIEWS_FILE" ]; then
    tail -c 1 "$VIEWS_FILE" | read -r _ || echo "" >> "$VIEWS_FILE"
fi
echo "✅ Archivo limpiado"
echo ""

# 4. Agregar stubs correctamente
echo "[4] Agregando stubs..."
cat >> "$VIEWS_FILE" << 'STUBS_EOF'

# --- HOTFIX: stubs para compatibilidad con urls.py ---
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.http import require_GET


def dashboard_ai_view(request, *args, **kwargs):
    return HttpResponse("Dashboard AI (stub).", status=200)


@require_GET
def revenue_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "revenue_analytics_api"}, status=200)


@require_GET
def vehicle_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "vehicle_analytics_api"}, status=200)


@require_GET
def clientes_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "clientes_analytics_api"}, status=200)


@require_GET
def predictive_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "predictive_analytics_api"}, status=200)


@require_GET
def real_time_metrics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "real_time_metrics_api"}, status=200)


class AIInsightView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"ok": False, "stub": "AIInsightView"}, status=200)


def export_report_view(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "export_report_view"}, status=200)
STUBS_EOF

echo "✅ Stubs agregados correctamente"
echo ""

# 5. Verificar sintaxis
echo "[5] Verificando sintaxis Python..."
if python3 -m py_compile "$VIEWS_FILE" 2>&1; then
    echo "✅ Sintaxis correcta"
else
    echo "❌ Error de sintaxis detectado"
    echo ""
    echo "Mostrando últimas 20 líneas del archivo:"
    tail -n 20 "$VIEWS_FILE"
    echo ""
    echo "¿Deseas restaurar el backup? (s/n)"
    read -r respuesta
    if [ "$respuesta" = "s" ]; then
        cp "$BACKUP_FILE" "$VIEWS_FILE"
        echo "✅ Backup restaurado"
    fi
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Proceso completado"
echo "=========================================="
echo ""
echo "Siguiente paso:"
echo "  sudo systemctl restart egarage-gunicorn"
echo "  sudo -u egarage -H bash -lc 'cd /srv/egarage && /srv/egarage/venv/bin/python manage.py check'"
