# --- HOTFIX: stubs para compatibilidad con urls.py ---
# Copiar y pegar este bloque al final de /srv/egarage/taller/analytics/views.py
#
# Comando rápido:
# sudo nano /srv/egarage/taller/analytics/views.py
# (ir al final del archivo y pegar esto)

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
