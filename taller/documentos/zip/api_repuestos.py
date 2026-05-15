"""
API de autocomplete para repuestos - Usado por Alpine.js
"""

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from taller.models.repuesto import Repuesto


@login_required
@require_GET
def buscar_repuestos_api(request):
    """
    API ligera para el autocomplete de Alpine.js.

    Busca por código (part_number) o nombre, filtrando por la empresa del usuario.
    Devuelve un array simple de resultados (sin paginación compleja).

    Endpoint: GET /taller/api/repuestos/buscar/?q=texto
    Returns: [
        {
            'id': 1,
            'codigo': 'FIL-001',
            'nombre': 'Filtro de Aceite',
            'precio': 12500.0,
            'stock': 5
        },
        ...
    ]
    """
    q = request.GET.get("q", "").strip()

    # Validar query mínima
    if len(q) < 2:
        return JsonResponse([], safe=False)

    # Obtener empresa del usuario (multi-tenant)
    try:
        empresa = request.user.empresa
        if not empresa:
            return JsonResponse([], safe=False)
    except AttributeError:
        return JsonResponse([], safe=False)

    # Búsqueda: Código (part_number) exacto O nombre parcial
    # Usar Q objects para búsqueda OR
    qs = (
        Repuesto.objects.filter(empresa=empresa)
        .filter(models.Q(part_number__icontains=q) | models.Q(nombre__icontains=q))
        .order_by("nombre")[:20]
    )  # Limitar a 20 resultados para velocidad

    # Serializar resultados
    results = []
    for r in qs:
        results.append(
            {
                "id": r.id,
                "codigo": r.part_number or "",  # part_number es el código
                "nombre": r.nombre or "",
                # Convertir Decimal a float para JSON
                "precio": float(r.precio_venta or 0),
                "stock": int(r.cantidad_stock or 0),
            }
        )

    return JsonResponse(results, safe=False)
