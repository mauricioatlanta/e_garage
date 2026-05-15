"""
Views para el Marketplace de eGarage
"""

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import ProductoCatalogo


@login_required
@require_GET
def api_buscar_precios_por_partnumber(request):
    """
    Endpoint de consulta rápida de precios por part_number.
    Devuelve los precios de referencia de todas las casas de repuestos
    que tienen ese part_number en su catálogo.

    Endpoint: GET /marketplace/api/precios/?part_number=XXXX
    Returns: {
        "part_number": "XXXX",
        "precios": [
            {
                "casa_repuestos": "Indra",
                "precio_referencia": 45000.00,
                "disponible": true,
                "precio_compra_minimo": null
            },
            ...
        ]
    }
    """
    import re

    # Extraer y normalizar part_number
    part_number_raw = request.GET.get("part_number", "").strip()

    if not part_number_raw:
        return JsonResponse({"error": "part_number es requerido"}, status=400)

    # Normalización robusta: trim, remover guiones/espacios, uppercase
    # Esto asegura match perfecto independientemente de cómo se escriba
    part_number_clean = re.sub(r"[\s\-_/]", "", part_number_raw).upper()

    if not part_number_clean or len(part_number_clean) < 2:
        return JsonResponse(
            {"error": "part_number debe tener al menos 2 caracteres después de normalización"},
            status=400,
        )

    # Obtener empresa del usuario (multi-tenant)
    try:
        empresa = request.user.empresa
        if not empresa:
            return JsonResponse({"error": "Usuario sin empresa"}, status=400)
    except AttributeError:
        return JsonResponse({"error": "Usuario no autenticado"}, status=401)

    # Clave de caché única por empresa y part_number normalizado
    cache_key = f"marketplace_precios_{empresa.id}_{part_number_clean}"

    # Intentar obtener del caché (1 hora de duración)
    precios_cached = cache.get(cache_key)
    if precios_cached is not None:
        return JsonResponse(
            {
                "part_number": part_number_clean,  # Retornar versión normalizada
                "precios": precios_cached,
                "total": len(precios_cached),
                "cached": True,
            }
        )

    # Buscar productos del catálogo con búsqueda robusta
    # Usamos __iexact para case-insensitive y normalizamos en la query
    # Nota: Django normaliza automáticamente con __iexact, pero normalizamos
    # el part_number en la BD también para consistencia
    productos = (
        ProductoCatalogo.objects.filter(
            empresa=empresa,
            part_number__iexact=part_number_clean,  # Búsqueda case-insensitive con part_number normalizado
            activo=True,  # Solo productos activos
        )
        .select_related("casa_repuestos")
        .order_by("precio_referencia")
    )

    # Serializar resultados
    precios = []
    for producto in productos:
        precios.append(
            {
                "casa_repuestos": producto.casa_repuestos.nombre,
                "precio_referencia": float(producto.precio_referencia),
                "disponible": producto.disponible,
                "precio_compra_minimo": (
                    float(producto.precio_compra_minimo) if producto.precio_compra_minimo else None
                ),
                "id": producto.id,
            }
        )

    # Guardar en caché por 1 hora (3600 segundos)
    cache.set(cache_key, precios, 3600)

    return JsonResponse(
        {
            "part_number": part_number_clean,  # Retornar versión normalizada
            "precios": precios,
            "total": len(precios),
            "cached": False,
        }
    )


@login_required
@require_GET
def api_producto_por_id(request, producto_id):
    """
    Endpoint para obtener un producto específico por ID.
    Útil cuando el usuario hace clic en una sugerencia de precio.
    """
    try:
        empresa = request.user.empresa
        if not empresa:
            return JsonResponse({"error": "Usuario sin empresa"}, status=400)
    except AttributeError:
        return JsonResponse({"error": "Usuario no autenticado"}, status=401)

    try:
        producto = ProductoCatalogo.objects.get(id=producto_id, empresa=empresa, activo=True)

        return JsonResponse(
            {
                "id": producto.id,
                "part_number": producto.part_number,
                "nombre": producto.nombre,
                "casa_repuestos": producto.casa_repuestos.nombre,
                "precio_referencia": float(producto.precio_referencia),
                "disponible": producto.disponible,
                "precio_compra_minimo": (
                    float(producto.precio_compra_minimo) if producto.precio_compra_minimo else None
                ),
            }
        )
    except ProductoCatalogo.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)
