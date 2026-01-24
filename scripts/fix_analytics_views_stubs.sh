#!/bin/bash
# Script para agregar stubs mínimos a taller/analytics/views.py
# Ejecutar en el servidor: sudo bash fix_analytics_views_stubs.sh

set -e

VIEWS_FILE="/srv/egarage/taller/analytics/views.py"

if [ ! -f "$VIEWS_FILE" ]; then
    echo "❌ Error: No se encontró $VIEWS_FILE"
    exit 1
fi

echo "=========================================="
echo "🔧 Agregando stubs a analytics/views.py"
echo "=========================================="
echo ""

# Verificar si ya tiene los stubs
if grep -q "# --- HOTFIX: stubs para compatibilidad con urls.py ---" "$VIEWS_FILE"; then
    echo "⚠️  Los stubs ya están presentes. ¿Deseas reemplazarlos? (s/n)"
    read -r respuesta
    if [ "$respuesta" != "s" ]; then
        echo "✅ Cancelado. Los stubs ya existen."
        exit 0
    fi
    # Eliminar stubs anteriores si existen
    sed -i '/# --- HOTFIX: stubs para compatibilidad con urls.py ---/,$d' "$VIEWS_FILE"
fi

echo "📝 Agregando stubs al final del archivo..."
echo ""

# Agregar los stubs al final del archivo
cat >> "$VIEWS_FILE" << 'EOF'

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
EOF

echo "✅ Stubs agregados correctamente"
echo ""
echo "📋 Verificando sintaxis Python..."
python3 -m py_compile "$VIEWS_FILE" && echo "✅ Sintaxis correcta" || echo "❌ Error de sintaxis"

echo ""
echo "=========================================="
echo "✅ Proceso completado"
echo "=========================================="
echo ""
echo "Siguiente paso:"
echo "  sudo systemctl restart egarage-gunicorn"
echo "  sudo -u egarage -H bash -lc 'cd /srv/egarage && /srv/egarage/venv/bin/python manage.py check'"
