# taller/views/api_catalogo.py
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from taller.models.catalogo import CatalogoModeloAuto


@require_http_methods(["GET"])
def api_marcas(request):
    """
    API para obtener marcas de vehículos con autocompletado
    GET /api/marcas/?q=ford
    """
    query = request.GET.get("q", "").strip()

    marcas = CatalogoModeloAuto.get_marcas_activas()

    if query:
        marcas = marcas.filter(Q(marca__icontains=query))

    # Limitar resultados
    marcas = marcas[:20]

    results = [{"id": marca["marca"], "text": marca["marca"]} for marca in marcas]

    return JsonResponse({"results": results, "pagination": {"more": False}})


@require_http_methods(["GET"])
def api_modelos(request):
    """
    API para obtener modelos de vehículos por marca
    GET /api/modelos/?marca=Ford&q=mustang
    """
    marca = request.GET.get("marca", "").strip()
    query = request.GET.get("q", "").strip()

    if not marca:
        return JsonResponse({"error": "Marca requerida"}, status=400)

    modelos = CatalogoModeloAuto.get_modelos_por_marca(marca)

    if query:
        modelos = modelos.filter(Q(modelo__icontains=query))

    # Limitar resultados
    modelos = modelos[:20]

    results = [{"id": modelo["modelo"], "text": modelo["modelo"]} for modelo in modelos]

    return JsonResponse({"results": results, "pagination": {"more": False}})


@require_http_methods(["GET"])
def api_estadisticas_catalogo(request):
    """
    API para obtener estadísticas del catálogo
    GET /api/catalogo/stats/
    """
    from django.db.models import Count

    total_modelos = CatalogoModeloAuto.objects.filter(activo=True).count()
    total_marcas = (
        CatalogoModeloAuto.objects.filter(activo=True)
        .values("marca")
        .distinct()
        .count()
    )

    # Top 10 marcas con más modelos
    top_marcas = (
        CatalogoModeloAuto.objects.filter(activo=True)
        .values("marca")
        .annotate(total=Count("modelo"))
        .order_by("-total")[:10]
    )

    return JsonResponse(
        {
            "total_modelos": total_modelos,
            "total_marcas": total_marcas,
            "top_marcas": list(top_marcas),
        }
    )
