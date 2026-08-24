"""
Endpoints API modernos para servicios con soporte completo de:
- Búsqueda inteligente por rubro
- Creación rápida desde documentos
- Filtrado por categorías/subcategorías
- Búsqueda sobre servicios de empresa
"""

import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from taller.models.configuracion import ConfiguracionEmpresa
from taller.servicios.models import (
    CategoriaServicio,
    Servicio,
    SubcategoriaServicio,
)

COUNTRY_LANGUAGE_MAP = {
    "CL": "es",
    "MX": "es",
    "VE": "es",
    "PE": "es",
    "US": "en",
    "BR": "pt",
}


def _detectar_pais(request):
    """Detecta el país desde la URL o request"""
    path = request.path or ""
    if "/us/" in path.lower():
        return "US"
    elif "/mx/" in path.lower():
        return "MX"
    elif "/br/" in path.lower():
        return "BR"
    return "CL"  # Default


@login_required
@require_GET
def api_buscar_servicios(request):
    """
    API mejorada para buscar servicios con filtrado inteligente por rubro.

    Query params:
    - q: Texto de búsqueda
    - categoria_id: Filtrar por categoría
    - subcategoria_id: Filtrar por subcategoría
    - limit: Límite de resultados (default: 20)
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"servicios": [], "total": 0})

    # Obtener configuración de la empresa
    try:
        config = empresa.config
        rubro_empresa = config.rubro_principal
    except ConfiguracionEmpresa.DoesNotExist:
        rubro_empresa = "WORKSHOP"  # Default

    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    query = (request.GET.get("q") or "").strip()
    categoria_id = request.GET.get("categoria_id")
    subcategoria_id = request.GET.get("subcategoria_id")
    limit = int(request.GET.get("limit", 20))

    # Base queryset: servicios de la empresa que estén activos
    servicios_qs = (
        Servicio.objects.filter(
            empresa=empresa,
            activo=True,
        )
        .select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
    )

    # Filtro inteligente por rubro: mostrar servicios cuyo rubro coincide
    # o es genérico, o tiene rubro_efectivo que coincide
    if rubro_empresa and rubro_empresa != "MIXED":
        servicios_qs = servicios_qs.filter(
            Q(rubro_sugerido=rubro_empresa)
            | Q(rubro_efectivo=rubro_empresa)
            | Q(rubro_sugerido__isnull=True)
            | Q(rubro_efectivo__isnull=True)
        )

    # Filtro por texto de búsqueda
    if query:
        servicios_qs = servicios_qs.filter(
            Q(nombre__icontains=query)
            | Q(descripcion__icontains=query)
            | Q(codigo_interno__icontains=query)
            | Q(names__label__icontains=query)
            | Q(names__aliases__icontains=query)
        ).distinct()

    # Filtro por categoría
    if categoria_id:
        try:
            servicios_qs = servicios_qs.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            pass

    # Filtro por subcategoría
    if subcategoria_id:
        try:
            servicios_qs = servicios_qs.filter(subcategoria_id=int(subcategoria_id))
        except (ValueError, TypeError):
            pass

    # Ordenar y limitar
    servicios_qs = servicios_qs.order_by("categoria__orden", "subcategoria__orden", "nombre")[
        :limit
    ]

    # Preparar datos para respuesta
    servicios_data = []
    for servicio in servicios_qs:
        nombre_localizado = servicio.get_label(language)

        servicios_data.append(
            {
                "id": servicio.id,
                "nombre": nombre_localizado,
                "nombre_raw": servicio.nombre,
                "descripcion": servicio.descripcion or "",
                "precio_base": str(servicio.precio_base) if servicio.precio_base else None,
                "duracion_estimada_min": servicio.duracion_estimada_min,
                "codigo_interno": servicio.codigo_interno or "",
                "categoria": {
                    "id": servicio.categoria.id if servicio.categoria else None,
                    "nombre": servicio.categoria.get_label(language) if servicio.categoria else "",
                    "code": servicio.categoria.code if servicio.categoria else "",
                },
                "subcategoria": {
                    "id": servicio.subcategoria.id if servicio.subcategoria else None,
                    "nombre": (
                        servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
                    ),
                    "code": servicio.subcategoria.code if servicio.subcategoria else "",
                },
            }
        )

    return JsonResponse(
        {
            "servicios": servicios_data,
            "total": len(servicios_data),
            "rubro_empresa": rubro_empresa,
        }
    )


@login_required
@require_POST
def api_crear_servicio_rapido(request):
    """
    API para crear un servicio rápidamente desde el documento.

    Body JSON:
    {
        "nombre": "Nombre del servicio",
        "categoria_id": 1,  # Opcional
        "subcategoria_id": 1,  # Opcional
        "precio_base": 100.00,  # Opcional
        "descripcion": "...",  # Opcional
    }

    Retorna el servicio creado con sus datos.
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"success": False, "error": "Usuario sin empresa asignada"}, status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    nombre = (payload.get("nombre") or "").strip()
    if not nombre:
        return JsonResponse(
            {"success": False, "error": "Nombre del servicio requerido"}, status=400
        )

    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    # Obtener o crear categoría/subcategoría por defecto si no se proporcionan
    categoria_id = payload.get("categoria_id")
    subcategoria_id = payload.get("subcategoria_id")

    if not categoria_id:
        # Buscar o crear categoría "Otros" o "Servicios Personalizados"
        categoria = CategoriaServicio.objects.filter(country=country).first()
        if not categoria:
            # Crear categoría por defecto
            categoria = CategoriaServicio.objects.create(
                country=country,
                code="CUSTOM",
                activo=True,
                orden=999,
            )
            from taller.servicios.models import CategoriaServicioName

            CategoriaServicioName.objects.create(
                categoria=categoria,
                language=language,
                label="Servicios Personalizados",
                is_default=True,
            )
    else:
        try:
            categoria = CategoriaServicio.objects.get(id=int(categoria_id), country=country)
        except (CategoriaServicio.DoesNotExist, ValueError, TypeError):
            return JsonResponse({"success": False, "error": "Categoría no válida"}, status=400)

    if not subcategoria_id:
        # Buscar o crear subcategoría "Otros"
        subcategoria = SubcategoriaServicio.objects.filter(
            categoria=categoria, country=country
        ).first()
        if not subcategoria:
            # Crear subcategoría por defecto
            subcategoria = SubcategoriaServicio.objects.create(
                categoria=categoria,
                country=country,
                code="CUSTOM_OTHER",
                activo=True,
                orden=999,
            )
            from taller.servicios.models import SubcategoriaServicioName

            SubcategoriaServicioName.objects.create(
                subcategoria=subcategoria,
                language=language,
                label="Otros Servicios",
                is_default=True,
            )
    else:
        try:
            subcategoria = SubcategoriaServicio.objects.get(
                id=int(subcategoria_id), categoria=categoria, country=country
            )
        except (SubcategoriaServicio.DoesNotExist, ValueError, TypeError):
            return JsonResponse({"success": False, "error": "Subcategoría no válida"}, status=400)

    # Verificar si ya existe un servicio con ese nombre en la misma empresa y categoría
    servicio_existente = Servicio.objects.filter(
        empresa=empresa,
        nombre=nombre,
        categoria=categoria,
    ).first()

    if servicio_existente:
        # Retornar el servicio existente
        nombre_localizado = servicio_existente.get_label(language)
        return JsonResponse(
            {
                "success": True,
                "servicio": {
                    "id": servicio_existente.id,
                    "nombre": nombre_localizado,
                    "nombre_raw": servicio_existente.nombre,
                    "precio_base": (
                        str(servicio_existente.precio_base)
                        if servicio_existente.precio_base
                        else None
                    ),
                    "categoria": {
                        "id": categoria.id,
                        "nombre": categoria.get_label(language),
                    },
                    "subcategoria": {
                        "id": subcategoria.id,
                        "nombre": subcategoria.get_label(language),
                    },
                },
                "ya_existia": True,
            }
        )

    # Crear nuevo servicio
    precio_base = payload.get("precio_base")
    descripcion = (payload.get("descripcion") or "").strip()

    servicio = Servicio.objects.create(
        empresa=empresa,
        nombre=nombre,
        categoria=categoria,
        subcategoria=subcategoria,
        descripcion=descripcion,
        activo=True,
    )

    # Procesar precio_base si se proporciona
    if precio_base is not None:
        try:
            servicio.precio_base = Decimal(str(precio_base))
            servicio.save(update_fields=["precio_base"])
        except (ValueError, InvalidOperation, TypeError):
            pass  # Ignorar si el precio no es válido

    # Obtener rubro de la empresa si existe
    try:
        config = empresa.config
        if config.rubro_principal:
            servicio.rubro_sugerido = config.rubro_principal
            servicio.save(update_fields=["rubro_sugerido"])
    except ConfiguracionEmpresa.DoesNotExist:
        pass

    nombre_localizado = servicio.get_label(language)

    return JsonResponse(
        {
            "success": True,
            "servicio": {
                "id": servicio.id,
                "nombre": nombre_localizado,
                "nombre_raw": servicio.nombre,
                "precio_base": str(servicio.precio_base) if servicio.precio_base else None,
                "descripcion": servicio.descripcion or "",
                "categoria": {
                    "id": categoria.id,
                    "nombre": categoria.get_label(language),
                },
                "subcategoria": {
                    "id": subcategoria.id,
                    "nombre": subcategoria.get_label(language),
                },
            },
            "ya_existia": False,
        }
    )


@login_required
@require_GET
def api_categorias_subcategorias(request):
    """
    API para obtener todas las categorías y subcategorías disponibles.
    Útil para poblar los selects en el modal de creación rápida.
    """
    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    categorias_qs = (
        CategoriaServicio.objects.filter(
            country=country,
            activo=True,
        )
        .prefetch_related("names", "subcategorias__names")
        .order_by("orden", "code")
    )

    categorias_data = []
    for categoria in categorias_qs:
        subcategorias_data = []
        for subcategoria in categoria.subcategorias.filter(activo=True).order_by("orden", "code"):
            subcategorias_data.append(
                {
                    "id": subcategoria.id,
                    "nombre": subcategoria.get_label(language),
                    "code": subcategoria.code or "",
                }
            )

        categorias_data.append(
            {
                "id": categoria.id,
                "nombre": categoria.get_label(language),
                "code": categoria.code or "",
                "icono": categoria.icono or "",
                "subcategorias": subcategorias_data,
            }
        )

    return JsonResponse(
        {
            "categorias": categorias_data,
        }
    )
