from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
from taller.models.marcas_usa import ModeloVehiculo
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio


# Endpoint para búsqueda AJAX de motores por modelo
def buscar_motores_api(request):
    # 🔒 FILTRO POR EMPRESA - Los motores no necesitan filtro por empresa (son globales)
    modelo_id = request.GET.get("modelo_id")
    motores = MotorVehiculo.objects.all()
    if modelo_id:
        motores = motores.filter(modelo_id=modelo_id)
    data = [{"id": m.pk, "nombre": m.nombre} for m in motores.order_by("nombre")[:100]]
    return JsonResponse(data, safe=False)


# Endpoint para búsqueda AJAX de cajas por modelo
def buscar_cajas_api(request):
    # 🔒 FILTRO POR EMPRESA - Las cajas no necesitan filtro por empresa (son globales)
    modelo_id = request.GET.get("modelo_id")
    cajas = CajaVehiculo.objects.all()
    if modelo_id:
        cajas = cajas.filter(modelo_id=modelo_id)
    data = [{"id": c.pk, "nombre": c.nombre} for c in cajas.order_by("nombre")[:100]]
    return JsonResponse(data, safe=False)


# Endpoint para búsqueda AJAX de modelos por marca
def buscar_modelos_api(request):
    # 🔒 FILTRO POR EMPRESA - Los modelos no necesitan filtro por empresa (son globales)
    marca_id = request.GET.get("marca_id")
    modelos = ModeloVehiculo.objects.all()
    if marca_id:
        modelos = modelos.filter(marca_id=marca_id)
    data = [{"id": m.pk, "nombre": m.nombre} for m in modelos.order_by("nombre")[:100]]
    return JsonResponse(data, safe=False)


import json

from django.views.decorators.csrf import csrf_exempt

from taller.models.tienda import Tienda


@login_required
def api_status(request):
    return JsonResponse({"status": "ok", "user": request.user.username})


@csrf_exempt
@login_required
def crear_tienda_api(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa

        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={"nombre_taller": f"Taller de {request.user.username}"},
        )

    if request.method == "GET":
        # Devolver información sobre el endpoint para requests GET
        return JsonResponse(
            {
                "message": "API para crear tiendas",
                "method": "POST",
                "required_fields": ["nombre"],
                "optional_fields": ["direccion", "telefono"],
                "example": {
                    "nombre": "Mi Tienda",
                    "direccion": "Calle 123",
                    "telefono": "555-1234",
                },
            }
        )

    elif request.method == "POST":
        data = json.loads(request.body)
        nombre = data.get("nombre")
        direccion = data.get("direccion", "")
        telefono = data.get("telefono", "")
        if not nombre:
            return JsonResponse({"error": "El nombre es obligatorio"}, status=400)

        # Crear tienda asociada a la empresa del usuario
        tienda = Tienda.objects.create(
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            empresa=empresa,  # 🔒 FILTRO EMPRESA
        )
        return JsonResponse({"id": tienda.pk, "nombre": tienda.nombre})

    else:
        return JsonResponse({"error": "Método no permitido"}, status=405)


# Endpoint para búsqueda AJAX de clientes
@login_required
@login_required
def buscar_clientes_api(request):
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa

        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={"nombre_taller": f"Taller de {request.user.username}"},
        )

    q = request.GET.get("q", "").strip()
    # FILTRAR SOLO CLIENTES DE LA EMPRESA DEL USUARIO
    clientes = Cliente.objects.filter(empresa=empresa)
    if q:
        clientes = clientes.filter(
            models.Q(nombre__icontains=q)
            | models.Q(apellido__icontains=q)
            | models.Q(email__icontains=q)
            | models.Q(tax_id__icontains=q)
        )
    data = [
        {
            "id": c.pk,
            "nombre": f"{c.nombre} {c.apellido or ''}".strip(),
            "identificador": c.tax_id or c.telefono or c.email or "",
            "email": c.email or "",
        }
        for c in clientes[:20]
    ]
    return JsonResponse({"results": data})


# === NUEVAS APIS PARA FORMULARIO FUTURISTA ===


@login_required
def vehiculos_cliente_api(request, cliente_id):
    """Obtiene vehículos de un cliente específico filtrados por empresa"""
    try:
        empresa = request.user.empresa
    except AttributeError:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    try:
        vehiculos = Vehiculo.objects.filter(
            cliente_id=cliente_id,
            cliente__empresa=empresa,  # 🔒 FILTRO CRÍTICO POR EMPRESA
        )

        data = [
            {
                "id": v.pk,
                "patente": getattr(v, "patente", ""),
                "vin": getattr(v, "vin", ""),
                "marca": getattr(v, "marca", "") or str(getattr(v, "marca_obj", "")),
                "modelo": getattr(v, "modelo", "") or str(getattr(v, "modelo_obj", "")),
                "año": getattr(v, "año", ""),
            }
            for v in vehiculos[:20]
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def repuesto_by_code_api(request):
    """Busca repuesto por código exacto"""
    try:
        empresa = request.user.empresa
    except AttributeError:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    code = request.GET.get("code", "").strip()
    if not code:
        return JsonResponse({"error": "Código requerido"}, status=400)

    try:
        repuesto = Repuesto.objects.filter(
            part_number__iexact=code, empresa=empresa  # 🔒 FILTRO CRÍTICO POR EMPRESA
        ).first()

        if not repuesto:
            return JsonResponse({"error": "Repuesto no encontrado"}, status=404)

        data = {
            "id": repuesto.pk,
            "codigo": repuesto.part_number,
            "nombre": getattr(repuesto, "nombre", ""),
            "precio_compra": float(getattr(repuesto, "precio_compra", 0)),
            "precio_venta_sugerido": float(getattr(repuesto, "precio_venta", 0)),
            "stock": getattr(repuesto, "cantidad_stock", 0),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def buscar_repuestos_api(request):
    """Busca repuestos por texto"""
    try:
        empresa = request.user.empresa
    except AttributeError:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    try:
        repuestos = Repuesto.objects.filter(
            empresa=empresa  # 🔒 FILTRO CRÍTICO POR EMPRESA
        )

        # Buscar por código o nombre
        repuestos = repuestos.filter(
            models.Q(part_number__icontains=q) | models.Q(nombre__icontains=q)
        )

        data = {
            "results": [
                {
                    "id": r.pk,
                    "codigo": r.part_number,
                    "nombre": getattr(r, "nombre", ""),
                    "precio_compra": float(getattr(r, "precio_compra", 0)),
                    "precio_venta_sugerido": float(getattr(r, "precio_venta", 0)),
                    "stock": getattr(r, "cantidad_stock", 0),
                }
                for r in repuestos[:20]
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def buscar_servicios_api(request):
    """Busca servicios por texto"""
    try:
        empresa = request.user.empresa
    except AttributeError:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    try:
        # Buscar en Servicio si existe
        servicios = []
        try:
            servicios = (
                Servicio.objects.filter(
                    empresa=empresa  # 🔒 FILTRO CRÍTICO POR EMPRESA
                )
                .filter(
                    models.Q(nombre__icontains=q)
                    | models.Q(categoria__names__label__icontains=q)
                )
                .distinct()
            )
        except Exception as e:
            print(f"Error buscando servicios: {e}")
            servicios = []

        data = {
            "results": [
                {
                    "id": s.pk if hasattr(s, "pk") else f"temp_{i}",
                    "nombre": getattr(s, "nombre", f"Servicio {i}"),
                    "categoria": str(getattr(s, "categoria", "General")),
                    "precio_sugerido": 0,  # El precio se ingresa manualmente
                }
                for i, s in enumerate(list(servicios)[:20])
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def buscar_otros_servicios_api(request):
    """Busca otros servicios (terceros)"""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    # Servicios de terceros de ejemplo
    servicios_ejemplo = [
        {"nombre": "Alineación", "proveedor_tipico": "Alineadora Central"},
        {"nombre": "Balanceado", "proveedor_tipico": "Alineadora Central"},
        {"nombre": "Rectificado", "proveedor_tipico": "Rectificadora Motors"},
        {"nombre": "Pintura", "proveedor_tipico": "Taller Pintura Pro"},
        {"nombre": "Tapicería", "proveedor_tipico": "Tapicería Express"},
    ]

    # Filtrar por query
    resultados = [s for s in servicios_ejemplo if q.lower() in s["nombre"].lower()]

    data = {
        "results": [
            {
                "id": f"ext_{i}",
                "nombre": s["nombre"],
                "proveedor_tipico": s["proveedor_tipico"],
            }
            for i, s in enumerate(resultados[:10])
        ]
    }
    return JsonResponse(data)


@login_required
def ops_metrics_api(request):
    """
    API endpoint para métricas operativas en tiempo real
    Devuelve KPIs para el Command Center
    """
    try:
        empresa = request.user.empresa
    except AttributeError:
        return JsonResponse({"error": "Usuario sin empresa"}, status=400)

    # Fechas de referencia
    hoy = timezone.now().date()
    ayer = hoy - timedelta(days=1)
    hace_7_dias = hoy - timedelta(days=7)

    # Documentos de hoy
    docs_today = Documento.objects.filter(empresa=empresa, fecha_emision=hoy).count()

    # Documentos de ayer para calcular delta
    docs_yesterday = Documento.objects.filter(
        empresa=empresa, fecha_emision=ayer
    ).count()

    # Calcular delta (porcentaje de cambio)
    if docs_yesterday > 0:
        docs_delta = (docs_today - docs_yesterday) / docs_yesterday
    else:
        docs_delta = 0.0 if docs_today == 0 else 1.0

    # Clientes únicos atendidos esta semana
    clients_week = (
        Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias)
        .values("cliente")
        .distinct()
        .count()
    )

    # Estado del sistema (siempre online por ahora)
    system_online = True
    system_msg = "All modules active"

    # Eficiencia: ratio de documentos "cerrados" vs emitidos
    # Consideramos "cerrados" los que tienen estado final o son facturas
    docs_cerrados = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__gte=hace_7_dias,
        tipo__in=["FAC", "OT"],  # Facturas y Órdenes de Trabajo como "cerrados"
    ).count()

    docs_totales_semana = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=hace_7_dias
    ).count()

    if docs_totales_semana > 0:
        efficiency = docs_cerrados / docs_totales_semana
    else:
        efficiency = 0.0

    return JsonResponse(
        {
            "docs_today": docs_today,
            "docs_delta": round(docs_delta, 2),  # Redondear a 2 decimales
            "clients_week": clients_week,
            "system_online": system_online,
            "system_msg": system_msg,
            "efficiency": round(efficiency, 2),  # Redondear a 2 decimales
        }
    )


def api_status(request):
    """Estado de la API"""
    return JsonResponse(
        {
            "status": "ok",
            "message": "API e_garage funcionando correctamente",
            "endpoints": [
                "/api/clientes/",
                "/api/vehiculos/<cliente_id>/",
                "/api/repuestos/by-code",
                "/api/repuestos/",
                "/api/servicios/",
                "/api/otros-servicios/",
                "/api/ops-metrics/",
            ],
        }
    )
