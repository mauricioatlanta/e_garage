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

    Busca por codigo (part_number), nombre o proveedor, filtrando por la empresa del usuario.
    Devuelve un array simple de resultados (sin paginacion compleja).

    Endpoint: GET /taller/api/repuestos/buscar/?q=texto
    Returns: [
        {
            'id': 1,
            'codigo': 'FIL-001',
            'nombre': 'Filtro de Aceite',
            'proveedor': 'ACME',
            'precio': 12500.0,
            'stock': 5
        },
        ...
    ]
    """
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    try:
        empresa = request.user.empresa
        if not empresa:
            return JsonResponse([], safe=False)
    except AttributeError:
        return JsonResponse([], safe=False)

    qs = (
        Repuesto.objects.filter(empresa=empresa)
        .filter(
            models.Q(part_number__icontains=q)
            | models.Q(nombre__icontains=q)
            | models.Q(proveedor__icontains=q)
        )
        .order_by("nombre")[:20]
    )

    results = []
    for repuesto in qs:
        results.append(
            {
                "id": repuesto.id,
                "codigo": repuesto.part_number or "",
                "nombre": repuesto.nombre or "",
                "proveedor": repuesto.proveedor or "",
                "precio": float(repuesto.precio_venta or 0),
                "stock": int(repuesto.cantidad_stock or 0),
            }
        )

    return JsonResponse(results, safe=False)
