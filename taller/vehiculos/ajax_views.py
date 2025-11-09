from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from taller.models.vehiculos import Modelo


@login_required
def modelos_por_marca(request):
    """Endpoint AJAX para obtener modelos filtrados por marca y opcionalmente por año"""
    marca_id = request.GET.get("marca")
    anio = request.GET.get("anio")

    # Filtrar por empresa del usuario
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"results": []})

    # Obtener país de la empresa
    country = getattr(empresa, "pais", "CL")

    # Query base
    qs = Modelo.objects.filter(country=country)

    if marca_id:
        qs = qs.filter(marca_id=marca_id)

    # Si el modelo tiene relación con año, aplica filtro:
    # (Nota: Modelo no tiene campo año directo, pero podrías agregarlo si necesitas)
    # if anio and hasattr(Modelo, "anio"):
    #     qs = qs.filter(anio=anio)

    # Ordenar y limitar resultados
    qs = qs.order_by("nombre")[:200]

    # Formatear datos
    data = [{"id": m.pk, "text": str(m), "nombre": m.nombre} for m in qs]

    return JsonResponse({"results": data})
