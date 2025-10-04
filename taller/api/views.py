from datetime import timedelta
import json

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
from taller.models.marcas_usa import ModeloVehiculo  # Asegúrate: este es el modelo correcto en USA
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio
from taller.models.tienda import Tienda


# ==========
# Helpers
# ==========
def _get_empresa(request):
    """Obtiene empresa del usuario autenticado."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return None
    return empresa


def _get_country(request, default="CL"):
    """País a partir de la empresa (CL/US)."""
    emp = _get_empresa(request)
    if not emp:
        return default
    return (getattr(emp, "pais", default) or default).upper()


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _paginate(qs, request, default_limit=None, max_limit=None):
    """Paginación configurable desde settings."""
    default_limit = default_limit or getattr(settings, "API_DEFAULT_LIMIT", 100)
    max_limit = max_limit or getattr(settings, "API_MAX_LIMIT", 200)
    
    limit = _parse_int(request.GET.get("limit")) or default_limit
    offset = _parse_int(request.GET.get("offset")) or 0
    limit = min(max(limit, 1), max_limit)
    offset = max(offset, 0)
    
    # Contar total antes de paginar
    total_count = qs.count()
    has_more = (offset + limit) < total_count
    
    return {
        'queryset': qs[offset : offset + limit],
        'pagination': {
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': has_more
        }
    }


def _format_item(obj, fmt="default"):
    """Formatea item para Select2 o formato estándar."""
    nombre = getattr(obj, "nombre", str(obj))
    if fmt == "select2":
        return {"id": obj.pk, "text": nombre}
    else:
        return {"id": obj.pk, "nombre": nombre}


def _get_modelo_cls(country: str):
    """Obtiene la clase del modelo según el país."""
    try:
        if country == "US":
            return apps.get_model("taller", "ModeloVehiculo")
        else:
            # Para Chile, usar el modelo común o específico
            return apps.get_model("taller", "ModeloVehiculo")
    except LookupError:
        # Fallback al import directo si no se encuentra en apps
        from taller.models.marcas_usa import ModeloVehiculo
        return ModeloVehiculo


# =========================================
# AJAX: Motores / Cajas / Modelos (USA/CL)
# =========================================

@login_required
@require_GET
def buscar_motores_api(request):
    """
    🔍 Motores por modelo (REQUERIDO). Catálogo filtrado por país/empresa.
    Respuesta: {"results":[{"id":..,"nombre":"..."}]} o {"results":[{"id":..,"text":"..."}]} para Select2
    """
    country = _get_country(request, "CL")
    empresa = _get_empresa(request)
    modelo_id = _parse_int(request.GET.get("modelo_id"))
    fmt = (request.GET.get("format") or "").lower()

    # modelo_id es REQUERIDO para evitar listados globales
    if not modelo_id:
        return JsonResponse({"results": [], "error": "modelo_id requerido"}, status=400)

    # Validar que el modelo_id pertenece al país/empresa
    Modelo = _get_modelo_cls(country)
    modelo_qs = Modelo.objects.filter(pk=modelo_id)
    if hasattr(Modelo, "country"):
        modelo_qs = modelo_qs.filter(country=country)
    if empresa and hasattr(Modelo, "empresa"):
        modelo_qs = modelo_qs.filter(empresa=empresa)
    if not modelo_qs.exists():
        return JsonResponse({"results": [], "error": "modelo_id inválido"}, status=400)

    qs = MotorVehiculo.objects.all()
    
    # Filtro por país (preferido)
    if hasattr(MotorVehiculo, "country"):
        qs = qs.filter(country=country)
    # Guardarraíl: filtrar por empresa si no hay campo country
    elif empresa and hasattr(MotorVehiculo, "empresa"):
        qs = qs.filter(empresa=empresa)

    # Filtrar por modelo_id (ahora validado)
    qs = qs.filter(modelo_id=modelo_id)

    # Soporte para búsqueda por texto
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(nombre__icontains=q)

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [_format_item(m, fmt) for m in paginated['queryset']]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


@login_required
@require_GET
def buscar_cajas_api(request):
    """
    🔍 Cajas por modelo (REQUERIDO). Catálogo filtrado por país/empresa.
    Respuesta: {"results":[{"id":..,"nombre":"..."}]} o {"results":[{"id":..,"text":"..."}]} para Select2
    """
    country = _get_country(request, "CL")
    empresa = _get_empresa(request)
    modelo_id = _parse_int(request.GET.get("modelo_id"))
    fmt = (request.GET.get("format") or "").lower()

    # modelo_id es REQUERIDO para evitar listados globales
    if not modelo_id:
        return JsonResponse({"results": [], "error": "modelo_id requerido"}, status=400)

    # Validar que el modelo_id pertenece al país/empresa
    Modelo = _get_modelo_cls(country)
    modelo_qs = Modelo.objects.filter(pk=modelo_id)
    if hasattr(Modelo, "country"):
        modelo_qs = modelo_qs.filter(country=country)
    if empresa and hasattr(Modelo, "empresa"):
        modelo_qs = modelo_qs.filter(empresa=empresa)
    if not modelo_qs.exists():
        return JsonResponse({"results": [], "error": "modelo_id inválido"}, status=400)

    qs = CajaVehiculo.objects.all()
    
    # Filtro por país (preferido)
    if hasattr(CajaVehiculo, "country"):
        qs = qs.filter(country=country)
    # Guardarraíl: filtrar por empresa si no hay campo country
    elif empresa and hasattr(CajaVehiculo, "empresa"):
        qs = qs.filter(empresa=empresa)

    # Filtrar por modelo_id (ahora validado)
    qs = qs.filter(modelo_id=modelo_id)

    # Soporte para búsqueda por texto
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(nombre__icontains=q)

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [_format_item(c, fmt) for c in paginated['queryset']]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


@login_required
@require_GET
def buscar_modelos_api(request):
    """
    🔍 Modelos por marca (opcional). Catálogo filtrado por país/empresa.
    Respuesta: {"results":[{"id":..,"nombre":"..."}]} o {"results":[{"id":..,"text":"..."}]} para Select2
    """
    country = _get_country(request, "CL")
    empresa = _get_empresa(request)
    marca_id = _parse_int(request.GET.get("marca_id"))
    fmt = (request.GET.get("format") or "").lower()

    # Usar modelo dinámico según país
    Modelo = _get_modelo_cls(country)
    qs = Modelo.objects.all()
    
    # Filtro por país (preferido)
    if hasattr(Modelo, "country"):
        qs = qs.filter(country=country)
    # Guardarraíl: filtrar por empresa si no hay campo country
    elif empresa and hasattr(Modelo, "empresa"):
        qs = qs.filter(empresa=empresa)

    if marca_id:
        qs = qs.filter(marca_id=marca_id)

    # Soporte para búsqueda por texto
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(nombre__icontains=q)

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [_format_item(m, fmt) for m in paginated['queryset']]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


# ===========================
# Salud del sistema / Status
# ===========================

@login_required
@require_GET
def api_status(request):
    return JsonResponse({"status": "ok", "user": request.user.username})


@require_GET
def api_root_status(request):
    """Estado público de la API (no colisiona con api_status autenticado)."""
    return JsonResponse(
        {
            "status": "ok",
            "message": "API e_garage funcionando correctamente",
            "endpoints": [
                "/api/status/",
                "/api/clientes/",
                "/api/vehiculos/<cliente_id>/",
                "/api/repuestos/by-code",
                "/api/repuestos/",
                "/api/servicios/",
                "/api/otros-servicios/",
                "/api/modelos/",
                "/api/motores/",
                "/api/cajas/",
                "/api/ops-metrics/",
                "/api/tiendas/crear/",
            ],
        }
    )


# ====================
# Crear Tienda (POST)
# ====================

@login_required
@require_POST
def crear_tienda_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    nombre = (payload.get("nombre") or "").strip()
    direccion = (payload.get("direccion") or "").strip()
    telefono = (payload.get("telefono") or "").strip()

    if not nombre:
        return JsonResponse({"error": "El nombre es obligatorio"}, status=400)

    # Evitar duplicados por nombre dentro de la empresa
    if Tienda.objects.filter(empresa=empresa, nombre__iexact=nombre).exists():
        return JsonResponse({"error": "Ya existe una tienda con ese nombre"}, status=409)

    tienda = Tienda.objects.create(
        nombre=nombre,
        direccion=direccion,
        telefono=telefono,
        empresa=empresa,
    )
    return JsonResponse({"id": tienda.pk, "nombre": tienda.nombre}, status=201)


# ==========================
# Búsqueda de entidades
# ==========================

@login_required
@require_GET
def buscar_clientes_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()
    country = _get_country(request, "CL")

    clientes = Cliente.objects.filter(empresa=empresa)
    if q:
        clientes = clientes.filter(
            models.Q(nombre__icontains=q)
            | models.Q(apellido__icontains=q)
            | models.Q(email__icontains=q)
            | models.Q(tax_id__icontains=q)
        )

    paginated = _paginate(clientes.order_by("nombre", "apellido"), request)
    
    # Etiqueta de identificador según país
    id_label = "RUT" if country == "CL" else "EIN"
    
    data = [
        {
            "id": c.pk,
            "nombre": f"{c.nombre} {c.apellido or ''}".strip(),
            "identificador": c.tax_id or c.telefono or c.email or "",
            "identificador_label": id_label,
            "email": c.email or "",
        }
        for c in paginated['queryset']
    ]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


@login_required
@require_GET
def info_cliente_api(request, cliente_id):
    """Obtiene información detallada de un cliente por ID"""
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    cid = _parse_int(cliente_id)
    if not cid:
        return JsonResponse({"error": "cliente_id inválido"}, status=400)

    try:
        cliente = Cliente.objects.get(pk=cid, empresa=empresa)
        return JsonResponse({
            "id": cliente.pk,
            "nombre": cliente.nombre,
            "apellido": cliente.apellido,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "tax_id": cliente.tax_id,
            "ciudad": str(cliente.ciudad) if cliente.ciudad else "",
        })
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente no encontrado"}, status=404)


@login_required
@require_GET
def vehiculos_cliente_api(request, cliente_id):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    cid = _parse_int(cliente_id)
    if not cid:
        return JsonResponse({"error": "cliente_id inválido"}, status=400)

    # Optimización: select_related para evitar N+1 queries
    qs = (Vehiculo.objects
          .filter(cliente_id=cid, cliente__empresa=empresa)  # 🔒 CRÍTICO
          .select_related("marca", "modelo")
          .order_by("-id"))

    paginated = _paginate(qs, request)
    
    def as_dict(v):
        return {
            "id": v.pk,
            "patente": getattr(v, "patente", "") or getattr(v, "placa", ""),
            "vin": getattr(v, "vin", ""),
            "marca": getattr(getattr(v, "marca", None), "nombre", "") or str(getattr(v, "marca", "") or ""),
            "modelo": getattr(getattr(v, "modelo", None), "nombre", "") or str(getattr(v, "modelo", "") or ""),
            "anio": getattr(v, "anio", getattr(v, "año", "")),
        }
    
    data = [as_dict(v) for v in paginated['queryset']]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


@login_required
@require_GET
def repuesto_by_code_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    code = (request.GET.get("code") or "").strip()
    if not code:
        return JsonResponse({"error": "Código requerido"}, status=400)

    r = (
        Repuesto.objects.filter(empresa=empresa, part_number__iexact=code)
        .order_by("-id")
        .first()
    )
    if not r:
        return JsonResponse({"error": "Repuesto no encontrado"}, status=404)

    data = {
        "id": r.pk,
        "codigo": r.part_number,
        "nombre": getattr(r, "nombre", ""),
        "precio_compra": float(getattr(r, "precio_compra", 0) or 0),
        "precio_venta_sugerido": float(getattr(r, "precio_venta", 0) or 0),
        "stock": getattr(r, "cantidad_stock", 0) or 0,
    }
    return JsonResponse(data)


@login_required
@require_GET
def buscar_repuestos_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    qs = Repuesto.objects.filter(empresa=empresa).filter(
        models.Q(part_number__icontains=q) | models.Q(nombre__icontains=q)
    )

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [
        {
            "id": r.pk,
            "codigo": r.part_number,
            "nombre": getattr(r, "nombre", ""),
            "precio_compra": float(getattr(r, "precio_compra", 0) or 0),
            "precio_venta_sugerido": float(getattr(r, "precio_venta", 0) or 0),
            "stock": getattr(r, "cantidad_stock", 0) or 0,
        }
        for r in paginated['queryset']
    ]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


@login_required
@require_GET
def buscar_servicios_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    qs = Servicio.objects.filter(empresa=empresa)
    
    # Feature-detect con hasattr para evitar except amplio
    if hasattr(Servicio, "categoria"):
        qs = qs.filter(
            models.Q(nombre__icontains=q) |
            models.Q(categoria__names__label__icontains=q)
        )
    else:
        qs = qs.filter(nombre__icontains=q)
    
    qs = qs.distinct().order_by("nombre")
    paginated = _paginate(qs, request)
    
    data = [
        {
            "id": getattr(s, "pk", None) or f"temp_{i}",
            "nombre": getattr(s, "nombre", f"Servicio {i}"),
            "categoria": str(getattr(s, "categoria", "General")),
            "precio_sugerido": 0,  # el precio se define en el documento
        }
        for i, s in enumerate(paginated['queryset'])
    ]
    return JsonResponse({
        "results": data,
        "pagination": paginated['pagination']
    })


@login_required
@require_GET
def buscar_otros_servicios_api(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    servicios_ejemplo = [
        {"nombre": "Alineación", "proveedor_tipico": "Alineadora Central"},
        {"nombre": "Balanceado", "proveedor_tipico": "Alineadora Central"},
        {"nombre": "Rectificado", "proveedor_tipico": "Rectificadora Motors"},
        {"nombre": "Pintura", "proveedor_tipico": "Taller Pintura Pro"},
        {"nombre": "Tapicería", "proveedor_tipico": "Tapicería Express"},
    ]
    resultados = [s for s in servicios_ejemplo if q.lower() in s["nombre"].lower()]

    data = [
        {
            "id": f"ext_{i}",
            "nombre": s["nombre"],
            "proveedor_tipico": s["proveedor_tipico"],
        }
        for i, s in enumerate(resultados)
    ]
    return JsonResponse({"results": data})


# ==========================
# KPIs / Command Center
# ==========================

@login_required
@require_GET
def ops_metrics_api(request):
    """
    KPIs en tiempo real.
    - Usa fecha_emision (estándar en tus KPIs)
    - 'cerrados' por estado final si existe; evita inferir por tipo.
    """
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    hoy = timezone.now().date()
    ayer = hoy - timedelta(days=1)
    hace_7_dias = hoy - timedelta(days=7)

    docs_today = Documento.objects.filter(
        empresa=empresa, fecha_emision=hoy
    ).count()

    docs_yesterday = Documento.objects.filter(
        empresa=empresa, fecha_emision=ayer
    ).count()

    docs_delta = (
        (docs_today - docs_yesterday) / docs_yesterday if docs_yesterday else (1.0 if docs_today else 0.0)
    )

    clients_week = (
        Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias)
        .values("cliente")
        .distinct()
        .count()
    )

    # Estados cerrados parametrizables por empresa (fallback a valores por defecto)
    estados_cerrados = ["CERRADO", "FACTURADO", "ENTREGADO"]
    # TODO: Implementar configuración por empresa cuando esté disponible
    # estados_cerrados = getattr(empresa.configuracion, "estados_cerrados", ["CERRADO", "FACTURADO", "ENTREGADO"])
    docs_cerrados = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__gte=hace_7_dias,
        estado__in=estados_cerrados,
    ).count()

    docs_totales_semana = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=hace_7_dias
    ).count()

    efficiency = (docs_cerrados / docs_totales_semana) if docs_totales_semana else 0.0

    return JsonResponse({
        "docs_today": docs_today,
        "docs_delta": round(docs_delta, 2),
        "clients_week": clients_week,
        "system_online": True,
        "system_msg": "All modules active",
        "efficiency": round(efficiency, 2),
    })