import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.models.pieza_desarme import ESTADO_DISPONIBLE, ESTADO_RESERVADA, PiezaDesarme
from taller.models.repuesto import Repuesto
from taller.models.tienda import Tienda
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio


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
        "queryset": qs[offset : offset + limit],
        "pagination": {
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
        },
    }


def _format_item(obj, fmt="default"):
    """Formatea item para Select2 o formato estándar."""
    nombre = getattr(obj, "nombre", str(obj))
    if fmt == "select2":
        return {"id": obj.pk, "text": nombre}
    else:
        return {"id": obj.pk, "nombre": nombre}


def _format_private_item(obj, fmt="default"):
    """Formatea item privado con ID prefijado para no colisionar con IDs globales."""
    item_id = f"empresa:{obj.pk}"
    nombre = getattr(obj, "nombre", str(obj))
    if fmt == "select2":
        return {"id": item_id, "text": nombre}
    return {"id": item_id, "nombre": nombre, "privado": True}


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
    # Usar modelos__id porque MotorVehiculo tiene relación ManyToMany con Modelo
    qs = qs.filter(modelos__id=modelo_id)

    # Soporte para búsqueda por texto
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(nombre__icontains=q)

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [_format_item(m, fmt) for m in paginated["queryset"]]
    if empresa:
        private_qs = MotorVehiculoEmpresa.objects.filter(
            empresa=empresa,
            modelo_id=modelo_id,
            country=country,
        )
        if q:
            private_qs = private_qs.filter(nombre__icontains=q)
        data.extend(_format_private_item(m, fmt) for m in private_qs.order_by("nombre"))
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


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
    # Usar modelos__id porque CajaVehiculo tiene relación ManyToMany con Modelo
    qs = qs.filter(modelos__id=modelo_id)

    # Soporte para búsqueda por texto
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(nombre__icontains=q)

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [_format_item(c, fmt) for c in paginated["queryset"]]
    if empresa:
        private_qs = CajaVehiculoEmpresa.objects.filter(
            empresa=empresa,
            modelo_id=modelo_id,
            country=country,
        )
        if q:
            private_qs = private_qs.filter(nombre__icontains=q)
        data.extend(_format_private_item(c, fmt) for c in private_qs.order_by("nombre"))
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


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
    data = [_format_item(m, fmt) for m in paginated["queryset"]]
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


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
        for c in paginated["queryset"]
    ]
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


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
        return JsonResponse(
            {
                "id": cliente.pk,
                "nombre": cliente.nombre,
                "apellido": cliente.apellido,
                "email": cliente.email,
                "telefono": cliente.telefono,
                "tax_id": cliente.tax_id,
                "ciudad": str(cliente.ciudad) if cliente.ciudad else "",
            }
        )
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
    qs = (
        Vehiculo.objects.filter(cliente_id=cid, cliente__empresa=empresa)  # 🔒 CRÍTICO
        .select_related("marca", "modelo")
        .order_by("-id")
    )

    paginated = _paginate(qs, request)

    def as_dict(v):
        return {
            "id": v.pk,
            "patente": getattr(v, "patente", "") or getattr(v, "placa", ""),
            "vin": getattr(v, "vin", ""),
            "marca": getattr(getattr(v, "marca", None), "nombre", "")
            or str(getattr(v, "marca", "") or ""),
            "modelo": getattr(getattr(v, "modelo", None), "nombre", "")
            or str(getattr(v, "modelo", "") or ""),
            "anio": getattr(v, "anio", getattr(v, "año", "")),
        }

    data = [as_dict(v) for v in paginated["queryset"]]
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


@login_required
@require_GET
def repuesto_by_code_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    code = (request.GET.get("code") or "").strip()
    if not code:
        return JsonResponse({"error": "Código requerido"}, status=400)

    r = Repuesto.objects.filter(empresa=empresa, part_number__iexact=code).order_by("-id").first()
    if not r:
        return JsonResponse({"error": "Repuesto no encontrado"}, status=404)

    data = {
        "id": r.pk,
        "codigo": r.part_number,
        "nombre": getattr(r, "nombre", ""),
        "proveedor": getattr(r, "proveedor", "") or "",
        "precio_compra": float(getattr(r, "precio_compra", 0) or 0),
        "precio_venta_sugerido": float(getattr(r, "precio_venta", 0) or 0),
        "stock": getattr(r, "cantidad_stock", 0) or 0,
        "stock_minimo": getattr(r, "stock_minimo", 0) or 0,
    }
    return JsonResponse(data)


@login_required
@require_GET
def buscar_repuestos_api(request, pais=None):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    qs = Repuesto.objects.filter(empresa=empresa).filter(
        models.Q(part_number__icontains=q)
        | models.Q(nombre__icontains=q)
        | models.Q(proveedor__icontains=q)
    )

    paginated = _paginate(qs.order_by("nombre"), request)
    data = [
        {
            "id": r.pk,
            "codigo": r.part_number,
            "nombre": getattr(r, "nombre", ""),
            "proveedor": getattr(r, "proveedor", "") or "",
            "precio_compra": float(getattr(r, "precio_compra", 0) or 0),
            "precio_venta_sugerido": float(getattr(r, "precio_venta", 0) or 0),
            "stock": getattr(r, "cantidad_stock", 0) or 0,
            "stock_minimo": getattr(r, "stock_minimo", 0) or 0,
        }
        for r in paginated["queryset"]
    ]
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


@login_required
@require_GET
def buscar_piezas_desarme_api(request):
    """API para buscar piezas de desarme disponibles (used parts) para agregar al documento."""
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()
    qs = (
        PiezaDesarme.objects.filter(empresa=empresa, activo=True)
        .filter(estado_pieza__in=[ESTADO_DISPONIBLE, ESTADO_RESERVADA])
        .filter(models.Q(cantidad__gt=0))
        .select_related("vehiculo")
    )

    if len(q) >= 2:
        qs = qs.filter(models.Q(codigo__icontains=q) | models.Q(nombre__icontains=q))

    paginated = _paginate(qs.order_by("codigo"), request)
    data = []
    for p in paginated["queryset"]:
        precio = float(p.precio_venta_sugerido or 0) or float(p.costo_asignado or 0)
        vehiculo_info = ""
        if p.vehiculo:
            vehiculo_info = (
                getattr(p.vehiculo, "patente", "") or getattr(p.vehiculo, "vin", "") or ""
            )
        data.append(
            {
                "id": p.pk,
                "codigo": p.codigo or "",
                "nombre": p.nombre or "",
                "precio": precio,
                "precio_venta_sugerido": precio,
                "cantidad": p.cantidad,
                "vehiculo_origen": vehiculo_info,
                "costo_asignado": float(p.costo_asignado or 0),
            }
        )
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


@login_required
@require_POST
def crear_repuesto_api(request):
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Usuario sin empresa"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    part_number = (payload.get("part_number") or "").strip()
    nombre = (payload.get("nombre") or "").strip()
    proveedor = (payload.get("proveedor") or "").strip()

    if not part_number:
        return JsonResponse({"success": False, "error": "Número de parte requerido"}, status=400)

    repuesto = (
        Repuesto.objects.filter(empresa=empresa, part_number__iexact=part_number)
        .order_by("-id")
        .first()
    )
    created = False

    if repuesto is None:
        if not nombre:
            return JsonResponse(
                {"success": False, "error": "Nombre del repuesto requerido"}, status=400
            )
        repuesto = Repuesto(empresa=empresa, part_number=part_number, nombre=nombre)
        created = True

    if created:
        precio_compra = payload.get("precio_compra")
        precio_venta = payload.get("precio_venta")
        if precio_compra is not None:
            try:
                repuesto.precio_compra = Decimal(str(precio_compra))
            except (TypeError, ValueError, InvalidOperation):
                repuesto.precio_compra = Decimal("0.00")
        if precio_venta is not None:
            try:
                repuesto.precio_venta = Decimal(str(precio_venta))
            except (TypeError, ValueError, InvalidOperation):
                repuesto.precio_venta = Decimal("0.00")
        if proveedor:
            repuesto.proveedor = proveedor
        repuesto.save()

    data = {
        "id": repuesto.pk,
        "codigo": repuesto.part_number or part_number,
        "nombre": repuesto.nombre or nombre,
        "precio_compra": float(repuesto.precio_compra or 0),
        "precio_venta": float(repuesto.precio_venta or 0),
        "proveedor": repuesto.proveedor or proveedor,
    }

    return JsonResponse({"success": True, "created": created, "repuesto": data})


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
            models.Q(nombre__icontains=q) | models.Q(categoria__names__label__icontains=q)
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
        for i, s in enumerate(paginated["queryset"])
    ]
    return JsonResponse({"results": data, "pagination": paginated["pagination"]})


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

    docs_today = Documento.objects.filter(empresa=empresa, fecha_emision=hoy).count()

    docs_yesterday = Documento.objects.filter(empresa=empresa, fecha_emision=ayer).count()

    docs_delta = (
        (docs_today - docs_yesterday) / docs_yesterday
        if docs_yesterday
        else (1.0 if docs_today else 0.0)
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

    return JsonResponse(
        {
            "docs_today": docs_today,
            "docs_delta": round(docs_delta, 2),
            "clients_week": clients_week,
            "system_online": True,
            "system_msg": "All modules active",
            "efficiency": round(efficiency, 2),
        }
    )


# ==========================================================
# API para Onboarding: Crear Clientes y Vehículos
# ==========================================================


@login_required
@require_POST
def api_crear_cliente_onboarding(request):
    """
    API para crear clientes desde el onboarding.
    POST /us/api/clientes/crear/ o /cl/api/clientes/crear/
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 60)
        logger.info("🚀 INICIO - API Crear Cliente Onboarding")
        logger.info(f"Usuario: {request.user.username}")

        empresa = _get_empresa(request)
        if not empresa:
            logger.error("❌ No se encontró empresa para el usuario")
            return JsonResponse({"success": False, "error": "No empresa found"}, status=400)

        logger.info(f"✅ Empresa encontrada: {empresa.nombre_taller} (ID: {empresa.id})")

        # Obtener datos del formulario
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        email = request.POST.get("email", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()

        # Campos USA
        estado_usa = request.POST.get("estado_usa", "").strip()
        ciudad_usa = request.POST.get("ciudad_usa", "").strip()
        zipcode = request.POST.get("zipcode", "").strip()

        logger.info(f"📝 Datos recibidos:")
        logger.info(f"   Nombre: {nombre}")
        logger.info(f"   Apellido: {apellido}")
        logger.info(f"   Email: {email}")
        logger.info(f"   Teléfono: {telefono}")
        logger.info(f"   Dirección: {direccion}")
        logger.info(f"   Estado USA: {estado_usa}")
        logger.info(f"   Ciudad USA: {ciudad_usa}")
        logger.info(f"   ZIP Code: {zipcode}")

        # Validaciones
        if not nombre or not apellido:
            logger.error("❌ Validación fallida: Nombre o apellido vacío")
            return JsonResponse(
                {"success": False, "error": "Nombre y apellido son requeridos"}, status=400
            )

        if not telefono:
            logger.error("❌ Validación fallida: Teléfono vacío")
            return JsonResponse({"success": False, "error": "Teléfono es requerido"}, status=400)

        # Verificar si ya existe un cliente con ese email en la empresa
        if email:
            if Cliente.objects.filter(empresa=empresa, email=email).exists():
                logger.error(f"❌ Ya existe cliente con email: {email}")
                return JsonResponse(
                    {"success": False, "error": "Ya existe un cliente con ese email"}, status=400
                )

        # Verificar qué campos tiene el modelo Cliente
        campos_disponibles = [f.name for f in Cliente._meta.get_fields()]
        logger.info(f"📋 Campos disponibles en Cliente: {campos_disponibles}")

        # Preparar datos para crear el cliente - SOLO campos que existen
        cliente_data = {
            "empresa": empresa,
            "nombre": nombre,
            "apellido": apellido,
            "telefono": telefono,
        }

        # Agregar email si existe y no está vacío
        if email:
            cliente_data["email"] = email

        # Agregar dirección si existe y no está vacía
        if direccion:
            cliente_data["direccion"] = direccion

        # Agregar ZIP code si el campo existe en el modelo
        if zipcode and "zipcode" in campos_disponibles:
            cliente_data["zipcode"] = zipcode
            logger.info(f"   ✅ ZIP Code agregado: {zipcode}")
        elif zipcode:
            logger.warning(f"   ⚠️ Campo 'zipcode' no existe en el modelo Cliente")

        # Agregar ciudad_usa si el campo existe en el modelo
        if ciudad_usa and "ciudad_usa" in campos_disponibles:
            cliente_data["ciudad_usa"] = ciudad_usa
            logger.info(f"   ✅ Ciudad USA agregada: {ciudad_usa}")
        elif ciudad_usa:
            logger.warning(f"   ⚠️ Campo 'ciudad_usa' no existe en el modelo Cliente")
            # Intentar agregarlo a dirección como fallback
            if direccion:
                cliente_data["direccion"] = f"{direccion}, {ciudad_usa}"
            else:
                cliente_data["direccion"] = ciudad_usa

        logger.info(f"📦 Creando cliente con datos finales: {cliente_data}")

        # Crear el cliente
        cliente = Cliente.objects.create(**cliente_data)

        logger.info(f"✅ Cliente creado exitosamente!")
        logger.info(f"   ID: {cliente.id}")
        logger.info(f"   Nombre: {cliente.nombre} {cliente.apellido}")
        logger.info(f"   Empresa: {cliente.empresa.nombre_taller}")

        # Verificar que se guardó
        cliente_verificado = Cliente.objects.filter(id=cliente.id, empresa=empresa).first()
        if cliente_verificado:
            logger.info(f"✅✅ VERIFICADO: Cliente existe en BD (ID: {cliente_verificado.id})")
        else:
            logger.error(f"❌❌ ERROR: Cliente NO se encuentra en BD después de crear!")

        return JsonResponse(
            {
                "success": True,
                "message": f"Cliente creado exitosamente (ID: {cliente.id})",
                "cliente": {
                    "id": cliente.id,
                    "nombre": cliente.nombre,
                    "apellido": cliente.apellido,
                    "email": cliente.email,
                    "telefono": cliente.telefono,
                },
            }
        )

    except Exception as e:
        import traceback

        logger.error("=" * 60)
        logger.error("❌❌❌ ERROR AL CREAR CLIENTE ❌❌❌")
        logger.error(f"Error: {str(e)}")
        logger.error("Traceback:")
        traceback.print_exc()
        logger.error("=" * 60)
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def api_crear_vehiculo_onboarding(request):
    """
    API para crear vehículos desde el onboarding.
    POST /us/api/vehiculos/crear/ o /cl/api/vehiculos/crear/
    """
    try:
        empresa = _get_empresa(request)
        if not empresa:
            return JsonResponse({"success": False, "error": "No empresa found"}, status=400)

        # Obtener datos del formulario
        cliente_id = request.POST.get("cliente_id")
        patente = request.POST.get("patente", "").strip().upper()
        marca_id = request.POST.get("marca_id")
        modelo_id = request.POST.get("modelo_id")
        anio = request.POST.get("anio")
        vin = request.POST.get("vin", "").strip()

        # Validaciones
        if not cliente_id:
            return JsonResponse({"success": False, "error": "Cliente es requerido"}, status=400)

        if not patente:
            return JsonResponse({"success": False, "error": "Patente es requerida"}, status=400)

        if not marca_id or not modelo_id or not anio:
            return JsonResponse(
                {"success": False, "error": "Marca, modelo y año son requeridos"}, status=400
            )

        # Verificar que el cliente existe y pertenece a la empresa
        try:
            cliente = Cliente.objects.get(id=cliente_id, empresa=empresa)
        except Cliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Cliente no encontrado"}, status=404)

        # Verificar si ya existe un vehículo con esa patente en la empresa
        if Vehiculo.objects.filter(empresa=empresa, patente=patente).exists():
            return JsonResponse(
                {"success": False, "error": "Ya existe un vehículo con esa patente"}, status=400
            )

        # Crear el vehículo
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        vehiculo = Vehiculo.objects.create(
            empresa=empresa,
            cliente=cliente,
            patente=patente,
            marca_id=marca_id,
            modelo_id=modelo_id,
            anio=int(anio),
            vin=vin or None,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Vehículo creado exitosamente",
                "vehiculo": {
                    "id": vehiculo.id,
                    "patente": vehiculo.patente,
                    "marca": vehiculo.marca.nombre if vehiculo.marca else "",
                    "modelo": vehiculo.modelo.nombre if vehiculo.modelo else "",
                    "anio": vehiculo.anio,
                },
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def api_procesar_foto_patente(request):
    """
    API endpoint para procesar foto de patente y buscar/crear vehículo.

    POST /api/vehiculos/procesar-foto-patente/
    Body: FormData con 'foto' (archivo de imagen)

    Returns JSON:
    {
        "success": true,
        "patente": "ABCD12",
        "vehiculo": {
            "id": 123,
            "patente": "ABCD12",
            "marca": "Toyota",
            "modelo": "Corolla",
            "cliente": {
                "id": 456,
                "nombre": "Juan Pérez"
            }
        },
        "existe": true,
        "mensaje": "Vehículo encontrado"
    }
    """
    import logging

    logger = logging.getLogger(__name__)

    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse(
            {"success": False, "error": "No tienes una empresa asignada"}, status=400
        )

    # Verificar que se subió un archivo
    if "foto" not in request.FILES:
        return JsonResponse({"success": False, "error": "No se recibió ninguna imagen"}, status=400)

    imagen = request.FILES["foto"]

    # Validar tipo de archivo
    if not imagen.content_type.startswith("image/"):
        return JsonResponse(
            {"success": False, "error": "El archivo debe ser una imagen"}, status=400
        )

    # Leer bytes de la imagen
    try:
        image_bytes = imagen.read()
        if len(image_bytes) == 0:
            return JsonResponse({"success": False, "error": "La imagen está vacía"}, status=400)
    except Exception as e:
        logger.error(f"Error leyendo imagen: {e}")
        return JsonResponse({"success": False, "error": "Error procesando la imagen"}, status=500)

    # OCR deshabilitado temporalmente
    return JsonResponse(
        {"success": False, "error": "OCR deshabilitado temporalmente en este servidor"},
        status=503,
    )


@login_required
@require_GET
def api_listar_clientes(request):
    """
    API para listar clientes de la empresa.
    GET /us/api/clientes/ o /cl/api/clientes/
    """
    try:
        empresa = _get_empresa(request)
        if not empresa:
            return JsonResponse([], safe=False)

        # Obtener todos los clientes de la empresa
        clientes = Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido")

        # Formatear la respuesta
        data = [
            {
                "id": c.id,
                "nombre": c.nombre,
                "apellido": c.apellido,
                "email": c.email or "",
                "telefono": c.telefono or "",
            }
            for c in clientes
        ]

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse([], safe=False)


@login_required
@require_POST
def api_completar_datos_facturacion(request, cliente_id):
    """
    API para completar datos de facturación de un cliente.

    Se usa cuando el mecánico intenta facturar y el cliente no tiene
    todos los datos requeridos. Abre un pop-up rápido para completar:
    - tax_id (identificador tributario)
    - giro (actividad económica)
    - billing_address (dirección)

    POST /us/api/clientes/<id>/completar-facturacion/ o /cl/api/clientes/<id>/completar-facturacion/
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        empresa = _get_empresa(request)
        if not empresa:
            return JsonResponse({"success": False, "error": "No empresa found"}, status=400)

        # Obtener el cliente
        cliente = get_object_or_404(Cliente, id=cliente_id, empresa=empresa)

        # Usar el formulario BillingDataForm
        from taller.clientes.forms_unified import BillingDataForm

        form = BillingDataForm(request.POST, instance=cliente, empresa=empresa)

        if form.is_valid():
            cliente = form.save()

            # Verificar que ahora está listo para facturar
            is_ready = cliente.is_billing_ready()
            missing = cliente.get_missing_billing_fields()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Datos de facturación completados exitosamente",
                    "cliente": {
                        "id": cliente.id,
                        "nombre": cliente.nombre,
                        "is_billing_ready": is_ready,
                        "profile_status": cliente.get_profile_status(),
                    },
                    "missing_fields": missing if not is_ready else [],
                }
            )
        else:
            # Retornar errores del formulario
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]

            return JsonResponse(
                {
                    "success": False,
                    "error": "Error al completar datos de facturación",
                    "form_errors": errors,
                },
                status=400,
            )

    except Exception as e:
        logger.error(f"Error en api_completar_datos_facturacion: {e}")
        return JsonResponse(
            {"success": False, "error": f"Error al completar datos: {str(e)}"}, status=500
        )


@login_required
@require_GET
def api_verificar_facturacion_cliente(request, cliente_id):
    """
    API para verificar si un cliente está listo para facturar.

    Retorna el estado del perfil y los campos faltantes.

    GET /us/api/clientes/<id>/verificar-facturacion/ o /cl/api/clientes/<id>/verificar-facturacion/
    """
    try:
        empresa = _get_empresa(request)
        if not empresa:
            return JsonResponse({"success": False, "error": "No empresa found"}, status=400)

        cliente = get_object_or_404(Cliente, id=cliente_id, empresa=empresa)

        profile_status = cliente.get_profile_status()
        is_ready = cliente.is_billing_ready()
        missing = cliente.get_missing_billing_fields()

        return JsonResponse(
            {
                "success": True,
                "cliente": {
                    "id": cliente.id,
                    "nombre": cliente.nombre,
                    "is_billing_ready": is_ready,
                    "profile_status": profile_status,
                },
                "missing_fields": missing,
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Error al verificar cliente: {str(e)}"}, status=500
        )
