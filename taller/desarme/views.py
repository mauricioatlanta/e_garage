# Vistas del módulo Desarme: vehículos tipo DESARME y piezas (solo empresa, tipo_uso=DESARME)

import json
import logging
import re
import uuid as _uuid
from decimal import Decimal
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from taller.auth.decorators_role import role_required
from django.db import IntegrityError, transaction
from django.db.models import Count, F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_GET, require_POST

from taller.models.empresa import Empresa
from taller.models.pieza_desarme import (
    ESTADO_DANADA,
    ESTADO_DISPONIBLE,
    ESTADO_FALTANTE,
    ESTADO_SCRAP,
    ESTADO_VENDIDA,
    ESTADO_RESERVADA,
    ESTADO_PIEZA_CHOICES,
    PiezaDesarme,
    PiezaDesarmeCompanyLabel,
)
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.vehiculo_desarme import ESTADO_DESARME_CHOICES, VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.models.inspeccion_ingreso import DanoInspeccion, InspeccionIngreso
from taller.models.vendedor_desarme import VendedorDesarme
from taller.documentos.views_migrated import _reverse_with_request
from taller.utils.empresa import get_user_empresa_safe
from .forms import PiezaDesarmeForm, PiezaSueltaForm, VehiculoDesarmeForm
from .services import _ensure_vehiculo_desarme
from taller.services.desarme_financial_service import calcular_ganancia_vehiculo

log = logging.getLogger(__name__)


def _normalize_phone(s):
    """Normaliza teléfono para comparación anti-duplicado."""
    if not s or not isinstance(s, str):
        return ""
    return re.sub(r"\D", "", s.strip())


@login_required
@require_GET
def api_vendedores_buscar(request):
    """Buscar vendedores por empresa. ?q= para filtrar por nombre/tel/email."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()[:100]
    qs = VendedorDesarme.objects.filter(empresa=empresa).order_by("nombre")

    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(telefono__icontains=q) | Q(email__icontains=q))[
            :20
        ]

    results = [
        {"id": str(v.id), "nombre": v.nombre, "telefono": v.telefono or "", "email": v.email or ""}
        for v in qs
    ]
    return JsonResponse({"results": results})


@login_required
@require_POST
def api_vendedor_crear(request):
    """
    Crear vendedor con validación anti-duplicado.
    Body: {nombre, telefono?, email?, direccion?, lugar_compra?, tax_id?}
    Si existe por nombre__iexact (o email/tel normalizado), devuelve el existente.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

    telefono = (data.get("telefono") or "").strip() or None
    email = (data.get("email") or "").strip() or None
    direccion = (data.get("direccion") or "").strip() or None
    lugar_compra = (data.get("lugar_compra") or "").strip() or None
    tax_id = (data.get("tax_id") or "").strip() or None

    # Anti-duplicado: buscar existente por nombre (case insensitive)
    existente = VendedorDesarme.objects.filter(empresa=empresa, nombre__iexact=nombre).first()

    if existente:
        return JsonResponse(
            {
                "success": True,
                "vendedor": {
                    "id": str(existente.id),
                    "nombre": existente.nombre,
                    "telefono": existente.telefono or "",
                    "email": existente.email or "",
                },
                "reused": True,
            }
        )

    # Por email (si se proporciona)
    if email:
        existente = VendedorDesarme.objects.filter(empresa=empresa, email__iexact=email).first()
        if existente:
            return JsonResponse(
                {
                    "success": True,
                    "vendedor": {
                        "id": str(existente.id),
                        "nombre": existente.nombre,
                        "telefono": existente.telefono or "",
                        "email": existente.email or "",
                    },
                    "reused": True,
                }
            )

    # Por teléfono normalizado (si se proporciona)
    if telefono:
        tel_norm = _normalize_phone(telefono)
        if tel_norm:
            for v in (
                VendedorDesarme.objects.filter(empresa=empresa)
                .exclude(telefono__isnull=True)
                .exclude(telefono="")
            ):
                if _normalize_phone(v.telefono) == tel_norm:
                    return JsonResponse(
                        {
                            "success": True,
                            "vendedor": {
                                "id": str(v.id),
                                "nombre": v.nombre,
                                "telefono": v.telefono or "",
                                "email": v.email or "",
                            },
                            "reused": True,
                        }
                    )

    # Crear nuevo
    vendedor = VendedorDesarme.objects.create(
        empresa=empresa,
        nombre=nombre,
        telefono=telefono,
        email=email,
        direccion=direccion,
        lugar_compra=lugar_compra,
        tax_id=tax_id,
    )
    return JsonResponse(
        {
            "success": True,
            "vendedor": {
                "id": str(vendedor.id),
                "nombre": vendedor.nombre,
                "telefono": vendedor.telefono or "",
                "email": vendedor.email or "",
            },
            "reused": False,
        }
    )


def _empresa_or_redirect(request):
    """Obtiene la empresa del usuario o redirige con error (acceso seguro a OneToOne)."""
    try:
        empresa = request.user.empresa if getattr(request.user, "is_authenticated", False) else None
    except Exception:
        empresa = None
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada.")
        return None
    return empresa


def _desarme_base_prefix(request):
    """
    Devuelve el prefijo país/idioma para desarme basado en la URL actual.
    Mantiene la misma lógica que los fallbacks en `urls_desarme.py`.
    """
    path_str = (request.path or "").strip("/")
    if "us/" in path_str or path_str.startswith("us"):
        return "/us/en"
    return "/cl/es"


def _auto_codigo_pieza(nombre, empresa, vehiculo_desarme):
    """Genera un código automático para una pieza nueva.

    Busca el nombre en el catálogo operativo para usar el código estándar
    (ej. 'Alternador' → 'MOT-01'). Si ya existe ese código para el mismo
    vehículo, añade sufijo -B, -C… Si no hay coincidencia en el catálogo
    genera 'PIE-XXXXXX'.
    """
    from .catalogo_operativo import get_catalogo_operativo_desarme

    nombre_lower = (nombre or "").strip().lower()
    catalogo = get_catalogo_operativo_desarme(empresa)
    base_codigo = None
    for item in catalogo:
        if item.get("nombre", "").strip().lower() == nombre_lower:
            base_codigo = item["codigo"]
            break

    if not base_codigo:
        return f"PIE-{_uuid.uuid4().hex[:6].upper()}"

    # Verificar unicidad dentro del mismo vehiculo_desarme
    existentes = set(
        PiezaDesarme.objects.filter(
            empresa=empresa,
            vehiculo_desarme=vehiculo_desarme,
            codigo__startswith=base_codigo,
        ).values_list("codigo", flat=True)
    )
    if base_codigo not in existentes:
        return base_codigo
    for letra in "BCDEFGHIJKLMNOPQRSTUVWXYZ":
        candidato = f"{base_codigo}-{letra}"
        if candidato not in existentes:
            return candidato
    return f"{base_codigo}-{_uuid.uuid4().hex[:4].upper()}"


def _desarme_url(request, suffix):
    """
    Construye una URL absoluta al módulo desarme respetando el prefijo país/idioma.
    """
    base = _desarme_base_prefix(request)
    suffix = str(suffix or "").lstrip("/")
    return f"{base}/desarme/{suffix}"


@login_required
def index(request):
    """Centro de operaciones del módulo Desarme: dashboard con KPIs, gráficos y navegación."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    base_qs = VehiculoDesarme.objects.filter(empresa=empresa)
    piezas_qs = PiezaDesarme.objects.filter(empresa=empresa)

    # KPIs — excluir placeholders del conteo de vehículos desarmados
    total_vehiculos = base_qs.filter(es_placeholder=False).count()
    total_piezas = piezas_qs.count()
    piezas_activas = piezas_qs.filter(activo=True).count()

    # Piezas por estado
    piezas_por_estado = dict(
        piezas_qs.filter(activo=True)
        .values("estado_pieza")
        .annotate(c=Count("id"))
        .values_list("estado_pieza", "c")
    )
    estado_labels = dict(ESTADO_PIEZA_CHOICES)
    chart_piezas_estado = [
        {"label": estado_labels.get(e, e), "count": piezas_por_estado.get(e, 0)}
        for e in [ESTADO_DISPONIBLE, ESTADO_RESERVADA, ESTADO_VENDIDA, ESTADO_DANADA, ESTADO_SCRAP]
    ]

    # Valor inventario (costo_asignado * cantidad)
    inventario_valor = piezas_qs.filter(activo=True).aggregate(
        v=Sum(F("costo_asignado") * F("cantidad"))
    )["v"] or Decimal("0")

    # Vehículos por mes (últimos 6 meses) — excluir placeholders
    seis_meses_atras = timezone.now().date() - timedelta(days=180)
    vehiculos_por_mes = (
        base_qs.filter(
            es_placeholder=False,
            fecha_ingreso_desarme__gte=seis_meses_atras,
            fecha_ingreso_desarme__isnull=False,
        )
        .annotate(mes=TruncMonth("fecha_ingreso_desarme"))
        .values("mes")
        .annotate(c=Count("id"))
        .order_by("mes")
    )
    chart_vehiculos_mes = [
        {"mes": v["mes"].strftime("%b %Y") if v["mes"] else "-", "count": v["c"]}
        for v in vehiculos_por_mes
    ]

    # Últimos vehículos con datos financieros para cards
    vehiculos_qs = (
        base_qs.select_related("marca", "modelo")
        .annotate(
            repuestos_count=Count("piezas_desarme"),
            piezas_disp=Count(
                "piezas_desarme",
                filter=Q(piezas_desarme__estado_pieza=ESTADO_DISPONIBLE, piezas_desarme__activo=True),
            ),
            piezas_vend=Count(
                "piezas_desarme",
                filter=Q(piezas_desarme__estado_pieza=ESTADO_VENDIDA),
            ),
        )
        .order_by("-fecha_ingreso_desarme", "-id")[:6]
    )

    ultimos_vehiculos = []
    for v in vehiculos_qs:
        ganancia = calcular_ganancia_vehiculo(v)
        total_piezas_v = (v.piezas_disp or 0) + (v.piezas_vend or 0)
        pct_vendido = int((v.piezas_vend or 0) / total_piezas_v * 100) if total_piezas_v > 0 else 0
        ultimos_vehiculos.append({
            "vehiculo": v,
            "ganancia": ganancia,
            "pct_vendido": pct_vendido,
            "piezas_disponibles": v.piezas_disp or 0,
            "repuestos_count": v.repuestos_count or 0,
        })

    # Repuestos recientes (últimos 5)
    ultimas_repuestos = piezas_qs.select_related("vehiculo_desarme").filter(activo=True).order_by("-id")[:5]

    return render(
        request,
        "taller/desarme/dashboard.html",
        {
            # Chrome del sitio (base.html) + panel interno más densos; solo esta URL.
            "eg_desarme_dashboard_compact": True,
            "empresa": empresa,
            "total_vehiculos": total_vehiculos,
            "total_repuestos": total_piezas,
            "repuestos_activas": piezas_activas,
            "inventario_valor": inventario_valor,
            "chart_repuestos_estado": chart_piezas_estado,
            "chart_vehiculos_mes": chart_vehiculos_mes,
            "ultimos_vehiculos": ultimos_vehiculos,
            "ultimas_repuestos": ultimas_repuestos,
        },
    )


def _ingresos_desarme_subquery():
    """Subquery: suma de (precio_unitario * cantidad) por vehículo en líneas de repuesto origen DESARME."""
    return (
        LineaRepuesto.objects.filter(
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme__vehiculo_desarme_id=OuterRef("pk"),
        )
        .values("pieza_desarme__vehiculo_desarme_id")
        .annotate(total=Sum(F("precio_unitario") * F("cantidad")))
        .values("total")
    )


@login_required
def lista_vehiculos(request):
    """Listado de vehículos de desarme con búsqueda, filtro por estado y conteo de piezas."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    ingresos_subq = _ingresos_desarme_subquery()
    qs = (
        VehiculoDesarme.objects.filter(empresa=empresa)
        .select_related("marca", "modelo", "color")
        .annotate(piezas_count=Count("piezas_desarme"))
        .annotate(
            ingresos_ventas=Coalesce(Subquery(ingresos_subq), Decimal("0.00")),
            costo_vehiculo=Coalesce(F("precio_compra"), Decimal("0.00")),
        )
        .annotate(ganancia=F("ingresos_ventas") - F("costo_vehiculo"))
        .order_by("-fecha_ingreso_desarme", "-id")
    )

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(patente__icontains=q)
            | Q(vin__icontains=q)
            | Q(marca_texto__icontains=q)
            | Q(modelo_texto__icontains=q)
            | Q(marca__nombre__icontains=q)
            | Q(modelo__nombre__icontains=q)
        )

    _VALID_ESTADOS = {c[0] for c in ESTADO_DESARME_CHOICES}
    estado_raw = request.GET.get("estado", "").strip()
    estado = estado_raw  # kept for template context (used in select + "Limpiar" check)
    valid_estados = [e for e in estado_raw.split(",") if e in _VALID_ESTADOS]
    if valid_estados:
        qs = qs.filter(estado_desarme__in=valid_estados)

    ingresado_antes_raw = request.GET.get("ingresado_antes", "").strip()
    if ingresado_antes_raw:
        from datetime import date as _date
        try:
            ingresado_antes = _date.fromisoformat(ingresado_antes_raw)
            qs = qs.filter(
                fecha_ingreso_desarme__isnull=False,
                fecha_ingreso_desarme__lt=ingresado_antes,
            )
        except ValueError:
            pass

    estados = (
        VehiculoDesarme.objects.filter(empresa=empresa)
        .exclude(estado_desarme__isnull=True)
        .exclude(estado_desarme="")
        .values_list("estado_desarme", flat=True)
        .distinct()
        .order_by("estado_desarme")
    )

    empresa_moneda = empresa.formato_moneda

    # Respuesta parcial para búsqueda en tiempo real (AJAX)
    if request.GET.get("partial") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "taller/desarme/lista_vehiculos_partial.html",
            {
                "vehiculos": qs,
                "q": q,
                "estado_filtro": estado,
                "empresa_moneda": empresa_moneda,
            },
        )

    return render(
        request,
        "taller/desarme/lista_vehiculos.html",
        {
            "vehiculos": qs,
            "empresa": empresa,
            "q": q,
            "estado_filtro": estado,
            "estados": list(estados),
            "empresa_moneda": empresa_moneda,
        },
    )


# Mapeo zona de inspección → códigos de catálogo afectados (legacy CL/MX y USA)
_ZONA_A_CODIGOS = {
    "capo":           ["CAR-01", "hood"],
    "maletero":       ["CAR-07", "trunk_lid"],
    "puerta_di":      ["CAR-02"],
    "puerta_dd":      ["CAR-03"],
    "puerta_ti":      ["CAR-04"],
    "puerta_td":      ["CAR-05"],
    "parachoque_del": ["CAR-08", "front_bumper_cover"],
    "parachoque_tra": ["CAR-09", "rear_bumper_cover"],
    "guardabarro_di": ["CAR-10", "fender"],
    "guardabarro_dd": ["CAR-11"],
    "guardabarro_ti": [],
    "guardabarro_td": [],
    "espejo_i":       ["CAR-14", "side_mirror"],
    "espejo_d":       ["CAR-15"],
    "vidrio_del":     ["CAR-16"],
    "vidrio_tra":     ["CAR-17"],
    "faro_di":        ["ILU-01", "headlight_left"],
    "faro_dd":        ["ILU-02", "headlight_right"],
    "faro_ti":        ["ILU-03", "tail_light_left"],
    "faro_td":        ["ILU-04", "tail_light_right"],
    "parrilla":       [],
    "techo":          [],
    "interior":       [],
}

# Tipos de daño que dejan la pieza no vendible
_TIPOS_EXCLUIR = {"faltante", "rotura", "golpe", "corrosion"}

# Todos los códigos gestionados automáticamente
_TODOS_CODIGOS = list({c for codes in _ZONA_A_CODIGOS.values() for c in codes})


def _sincronizar_estado_piezas(vehiculo, empresa, zonas):
    """
    Actualiza estado_pieza de PiezaDesarme según daños de la inspección.
    - faltante  → FALTANTE
    - rotura/golpe/corrosion → DANADA
    - zonas sin daño crítico → vuelven a DISPONIBLE
    zonas: list of (zona_code, tipo_dano, descripcion)
    """
    # Construir mapa código → estado destino
    codigos_nuevo_estado = {}
    for zona, tipo, _ in zonas:
        for codigo in _ZONA_A_CODIGOS.get(zona, []):
            if tipo == "faltante":
                codigos_nuevo_estado[codigo] = ESTADO_FALTANTE
            elif tipo in _TIPOS_EXCLUIR:
                if codigos_nuevo_estado.get(codigo) != ESTADO_FALTANTE:
                    codigos_nuevo_estado[codigo] = ESTADO_DANADA

    # Resetear piezas que ya no tienen daño crítico (solo si están en DANADA o FALTANTE)
    codigos_a_resetear = [c for c in _TODOS_CODIGOS if c not in codigos_nuevo_estado]
    if codigos_a_resetear:
        PiezaDesarme.objects.filter(
            vehiculo_desarme=vehiculo,
            empresa=empresa,
            codigo__in=codigos_a_resetear,
            estado_pieza__in=[ESTADO_DANADA, ESTADO_FALTANTE],
        ).update(estado_pieza=ESTADO_DISPONIBLE)

    # Aplicar estados nuevos
    for codigo, estado in codigos_nuevo_estado.items():
        PiezaDesarme.objects.filter(
            vehiculo_desarme=vehiculo,
            empresa=empresa,
            codigo=codigo,
        ).exclude(
            estado_pieza__in=[ESTADO_VENDIDA, ESTADO_SCRAP],  # no tocar vendidas/scrap
        ).update(estado_pieza=estado)


def _guardar_danos_carroceria(request, vehiculo, empresa):
    """Crea/reemplaza la InspeccionIngreso de un vehículo de desarme con los daños del POST."""
    zonas = []
    i = 0
    while f"zona_{i}" in request.POST:
        zona = request.POST.get(f"zona_{i}", "").strip()
        tipo = request.POST.get(f"tipo_dano_{i}", "").strip()
        desc = request.POST.get(f"descripcion_{i}", "").strip()
        if zona and tipo:
            zonas.append((zona, tipo, desc))
        i += 1

    # Sincronizar estados de piezas (incluso si zonas está vacío → resetea todo)
    _sincronizar_estado_piezas(vehiculo, empresa, zonas)

    if not zonas:
        return

    # vehiculo acá siempre es un VehiculoDesarme (crear_vehiculo/editar_vehiculo ya
    # cortaron a ese modelo). InspeccionIngreso.vehiculo exige un Vehiculo real
    # (on_delete=PROTECT, no nullable) -- usar el campo nuevo vehiculo_desarme
    # en su lugar, dejando vehiculo=None (no hay Vehiculo legacy detrás).
    if isinstance(vehiculo, VehiculoDesarme):
        lookup = {"vehiculo_desarme": vehiculo, "vehiculo": None, "documento": None}
    else:
        lookup = {"vehiculo": vehiculo, "vehiculo_desarme": None, "documento": None}
    inspeccion, _ = InspeccionIngreso.objects.update_or_create(
        **lookup,
        defaults={
            "empresa": empresa,
            "realizada_por": request.user,
            "estado_inspeccion": "completada",
        },
    )
    inspeccion.danos.all().delete()
    DanoInspeccion.objects.bulk_create([
        DanoInspeccion(inspeccion=inspeccion, zona=zona, tipo_dano=tipo, descripcion=desc)
        for zona, tipo, desc in zonas
    ])


@login_required
def crear_vehiculo(request):
    """Alta de vehículo de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    if request.method == "POST":
        form = VehiculoDesarmeForm(request.POST, request.FILES, empresa=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa
                    vehiculo.save()
                    _guardar_danos_carroceria(request, vehiculo, empresa)
                messages.success(
                    request, f"Vehículo de desarme {vehiculo.patente or vehiculo.vin} creado."
                )
                # No genera piezas en BD — el usuario las confirma en /revisar/
                try:
                    from .services import inicializar_sugerencias
                    inicializar_sugerencias(vehiculo, empresa)
                except Exception as inv_err:
                    log.exception("Error inicializando sugerencias para vehículo pk=%s", vehiculo.pk)
                    messages.warning(request, f"Vehículo guardado, pero falló la carga del catálogo: {inv_err}")
                return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/revisar/"))
            except IntegrityError:
                messages.error(
                    request, "Ya existe un vehículo con ese VIN o patente en esta empresa."
                )
            except Exception as e:
                log.exception("Error creando vehículo de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = VehiculoDesarmeForm(empresa=empresa)

    return render(
        request,
        "taller/desarme/vehiculo_form.html",
        {"form": form, "empresa": empresa, "titulo": "Nuevo vehículo de desarme", "empresa_moneda": empresa.formato_moneda},
    )


@login_required
def ver_vehiculo(request, pk):
    """Detalle rediseñado: cabecera, compra, resumen piezas, P&L y recientes. Solo propietario."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    es_propietario = getattr(empresa, "user_id", None) == request.user.id
    if not es_propietario and not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acceso restringido al propietario de la cuenta.")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]

    piezas = list(
        vehiculo.piezas_desarme.filter(activo=True)
        .prefetch_related("names", "company_labels")
        .order_by("codigo")
    )
    for p in piezas:
        p.display_nombre = p.get_display_label(empresa=empresa, language=lang)

    disponibles = sum(1 for p in piezas if p.estado_pieza == ESTADO_DISPONIBLE)
    vendidas = vehiculo.piezas_desarme.filter(estado_pieza=ESTADO_VENDIDA).count()
    danadas = sum(1 for p in piezas if p.estado_pieza == ESTADO_DANADA)
    faltantes = sum(1 for p in piezas if p.estado_pieza == ESTADO_FALTANTE)
    total_piezas_count = disponibles + vendidas + danadas + faltantes

    valor_potencial = sum(
        (p.precio_venta_sugerido or Decimal("0")) * p.cantidad
        for p in piezas
        if p.estado_pieza in (ESTADO_DISPONIBLE, ESTADO_RESERVADA)
    )

    costo_compra = vehiculo.precio_compra or Decimal("0")
    costo_transporte = vehiculo.transporte_grua_desarme or Decimal("0")
    costo_otros = vehiculo.otros_gastos_desarme or Decimal("0")
    costo_total = costo_compra + costo_transporte + costo_otros

    total_recaudado = (
        LineaRepuesto.objects.filter(
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme__vehiculo_desarme=vehiculo,
        ).aggregate(total=Sum(F("precio_unitario") * F("cantidad")))["total"]
        or Decimal("0")
    )

    ganancia_neta = total_recaudado - costo_total
    proyeccion_total = total_recaudado + valor_potencial - costo_total
    monto_chatarra = vehiculo.monto_chatarra or Decimal("0")
    es_dado_de_baja = bool(vehiculo.fecha_baja_desarme)
    ganancia_final = (
        total_recaudado + monto_chatarra - costo_total if es_dado_de_baja else ganancia_neta
    )

    repuestos_recientes = list(
        vehiculo.piezas_desarme.filter(activo=True)
        .prefetch_related("names", "company_labels")
        .order_by("-id")[:5]
    )
    for p in repuestos_recientes:
        p.display_nombre = p.get_display_label(empresa=empresa, language=lang)

    from taller.desarme.selectors.vehiculo_operaciones import get_vehicle_operations_summary
    ops_summary = get_vehicle_operations_summary(
        empresa=empresa,
        vehiculo=vehiculo,
        user=request.user,
        request=request,
    )

    return render(
        request,
        "taller/desarme/ver_vehiculo.html",
        {
            "vehiculo": vehiculo,
            "piezas": piezas,
            "empresa": empresa,
            "empresa_moneda": empresa.formato_moneda,
            "es_dado_de_baja": es_dado_de_baja,
            "es_superusuario": request.user.is_superuser,
            "disponibles": disponibles,
            "vendidas": vendidas,
            "danadas": danadas,
            "faltantes": faltantes,
            "total_piezas_count": total_piezas_count,
            "valor_potencial": valor_potencial,
            "costo_total": costo_total,
            "costo_compra": costo_compra,
            "costo_transporte": costo_transporte,
            "costo_otros": costo_otros,
            "total_recaudado": total_recaudado,
            "ganancia_neta": ganancia_neta,
            "proyeccion_total": proyeccion_total,
            "monto_chatarra": monto_chatarra,
            "ganancia_final": ganancia_final,
            "repuestos_recientes": repuestos_recientes,
            "ops": ops_summary,
        },
    )


@login_required
@require_POST
def dar_de_baja_vehiculo(request, pk):
    """Marca un vehículo de desarme como dado de baja. Solo para el propietario de la cuenta."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    es_propietario = getattr(empresa, "user_id", None) == request.user.id
    if not es_propietario and not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acceso restringido al propietario de la cuenta.")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    if vehiculo.fecha_baja_desarme:
        messages.warning(request, "Este vehículo ya está dado de baja.")
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/"))

    from decimal import InvalidOperation as _InvalidOp

    monto_raw = request.POST.get("monto_chatarra", "").strip().replace(".", "").replace(",", "")
    try:
        monto = Decimal(monto_raw) if monto_raw else Decimal("0")
        if monto < 0:
            monto = Decimal("0")
    except (_InvalidOp, ValueError):
        monto = Decimal("0")

    observaciones = request.POST.get("observaciones_baja", "").strip()

    vehiculo.fecha_baja_desarme = timezone.now().date()
    vehiculo.monto_chatarra = monto
    update_fields = ["fecha_baja_desarme", "monto_chatarra"]
    if observaciones:
        existing = (vehiculo.observaciones_desarme or "").rstrip()
        sep = "\n" if existing else ""
        vehiculo.observaciones_desarme = f"{existing}{sep}[BAJA] {observaciones}"
        update_fields.append("observaciones_desarme")
    vehiculo.save(update_fields=update_fields)

    messages.success(request, f"Vehículo dado de baja el {vehiculo.fecha_baja_desarme}.")
    return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/"))


@login_required
def editar_vehiculo(request, pk):
    """Edición de vehículo de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    if request.method == "POST":
        form = VehiculoDesarmeForm(request.POST, request.FILES, instance=vehiculo, empresa=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    _guardar_danos_carroceria(request, vehiculo, empresa)
                messages.success(request, "Vehículo actualizado.")
                return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/"))
            except IntegrityError:
                messages.error(
                    request, "Ya existe un vehículo con ese VIN o patente en esta empresa."
                )
            except Exception as e:
                log.exception("Error actualizando vehículo de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = VehiculoDesarmeForm(instance=vehiculo, empresa=empresa)

    return render(
        request,
        "taller/desarme/vehiculo_form.html",
        {
            "form": form,
            "vehiculo": vehiculo,
            "empresa": empresa,
            "titulo": "Editar vehículo de desarme",
            "empresa_moneda": empresa.formato_moneda,
        },
    )


@login_required
def lista_piezas(request):
    """Listado de piezas con búsqueda por código/nombre y filtros por estado y vehículo."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    piezas = (
        PiezaDesarme.objects.filter(empresa=empresa)
        .select_related("vehiculo_desarme", "vehiculo_desarme__marca", "vehiculo_desarme__modelo")
        .order_by("vehiculo_desarme__patente", "codigo")
    )

    q = request.GET.get("q", "").strip()
    if q:
        for term in q.split():
            piezas = piezas.filter(
                Q(codigo__icontains=term)
                | Q(nombre__icontains=term)
                | Q(vehiculo_desarme__patente__icontains=term)
                | Q(vehiculo_desarme__vin__icontains=term)
                | Q(vehiculo_desarme__marca_texto__icontains=term)
                | Q(vehiculo_desarme__modelo_texto__icontains=term)
                | Q(vehiculo_desarme__marca__nombre__icontains=term)
                | Q(vehiculo_desarme__modelo__nombre__icontains=term)
            )

    estado = request.GET.get("estado", "").strip()
    if estado:
        piezas = piezas.filter(estado_pieza=estado)

    vehiculo_id = request.GET.get("vehiculo", "").strip()
    if vehiculo_id:
        piezas = piezas.filter(vehiculo_desarme_id=vehiculo_id)

    if request.GET.get("sin_foto") == "1":
        piezas = piezas.filter(Q(imagen__isnull=True) | Q(imagen=""))

    if request.GET.get("sin_precio") == "1":
        piezas = piezas.filter(
            Q(precio_venta_sugerido__isnull=True) & Q(precio_sugerido__isnull=True)
        )

    if request.GET.get("sin_ubicacion") == "1":
        piezas = piezas.filter(ubicacion_fisica__isnull=True)

    _vqs = (
        VehiculoDesarme.objects.filter(empresa=empresa)
        .select_related("marca", "modelo")
        .order_by("patente", "vin")
    )
    vehiculos_choices = []
    for v in _vqs:
        tag = v.patente or v.vin or str(v.id)
        parts = []
        if v.anio:
            parts.append(str(v.anio))
        parts.append(v.get_marca_display())
        parts.append(v.get_modelo_display())
        parts.append(tag)
        vehiculos_choices.append((v.id, " · ".join(parts)))
    from taller.models.pieza_desarme import ESTADO_PIEZA_CHOICES

    return_to = request.GET.get("return_to", "").strip()
    select_field = request.GET.get("select_field", "").strip()

    return render(
        request,
        "taller/desarme/lista_piezas.html",
        {
            "piezas": piezas,
            "empresa": empresa,
            "q": q,
            "estado_filtro": estado,
            "vehiculo_filtro": vehiculo_id,
            "vehiculos_choices": vehiculos_choices,
            "estado_pieza_choices": ESTADO_PIEZA_CHOICES,
            "return_to": return_to,
            "select_field": select_field,
        },
    )


@login_required
@role_required("Owner", "Admin")
def crear_pieza(request):
    """Alta de pieza de desarme. Opcional ?vehiculo=<id> para pre-seleccionar vehículo."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = None
    vehiculo_id = request.GET.get("vehiculo")
    if vehiculo_id:
        vehiculo = VehiculoDesarme.objects.filter(
            pk=vehiculo_id,
            empresa=empresa,
        ).first()

    if request.method == "POST":
        form = PiezaDesarmeForm(request.POST, empresa=empresa, vehiculo=vehiculo)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pieza = form.save(commit=False)
                    pieza.empresa = empresa
                    if not pieza.codigo:
                        pieza.codigo = _auto_codigo_pieza(
                            pieza.nombre, empresa, pieza.vehiculo_desarme
                        )
                    pieza.save()
                messages.success(request, f"Pieza {pieza.codigo} creada.")
                if pieza.vehiculo_desarme_id:
                    return redirect(
                        _desarme_url(request, f"vehiculos/{pieza.vehiculo_desarme_id}/inventario-inteligente/")
                    )
                return redirect(_desarme_url(request, "piezas/"))
            except IntegrityError:
                messages.error(
                    request,
                    f"Ya existe una pieza con el código "
                    f"'{form.cleaned_data.get('codigo', '')}' en este vehículo. "
                    "Usa otro código.",
                )
            except Exception as e:
                log.exception("Error creando pieza de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = PiezaDesarmeForm(empresa=empresa, vehiculo=vehiculo)

    return render(
        request,
        "taller/desarme/pieza_form.html",
        {
            "form": form,
            "empresa": empresa,
            "vehiculo": vehiculo,
            "titulo": "Nueva pieza de desarme",
        },
    )


@login_required
@role_required("Owner", "Admin")
def crear_pieza_suelta(request):
    """Registra una pieza suelta sin vehículo completo. Crea un Vehiculo placeholder automáticamente."""
    import uuid as _uuid

    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    if request.method == "POST":
        form = PiezaSueltaForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            marca = d.get("marca_texto") or ""
            modelo = d.get("modelo_texto") or ""
            anio = d.get("anio_origen")

            partes = [p for p in [marca, modelo, str(anio) if anio else ""] if p]
            origen_label = " ".join(partes) if partes else "sin especificar"

            try:
                with transaction.atomic():
                    patente_sintetica = f"SLT-{_uuid.uuid4().hex[:12]}"
                    vehiculo = VehiculoDesarme.objects.create(
                        empresa=empresa,
                        es_placeholder=True,
                        patente=patente_sintetica,
                        marca_texto=marca or "",
                        modelo_texto=modelo or "",
                        anio=anio,
                    )
                    codigo = d.get("codigo") or f"SLT-{_uuid.uuid4().hex[:8].upper()}"
                    pieza = PiezaDesarme.objects.create(
                        empresa=empresa,
                        vehiculo_desarme=vehiculo,
                        nombre=d["nombre"],
                        codigo=codigo,
                        condicion=d["condicion"],
                        cantidad=d.get("cantidad") or 1,
                        precio_venta_sugerido=d.get("precio_venta_sugerido"),
                        imagen=d.get("imagen"),
                    )
                messages.success(request, f"Pieza «{pieza.nombre}» registrada (origen: {origen_label}).")
                return redirect(_desarme_url(request, "piezas/"))
            except IntegrityError:
                codigo_display = d.get("codigo") or "(auto)"
                messages.error(
                    request,
                    f"Ya existe una pieza con el código '{codigo_display}' en tu empresa. "
                    "Usa otro código o deja el campo vacío para generar uno automático.",
                )
            except Exception:
                log.exception("Error creando pieza suelta")
                messages.error(request, "Error al guardar la pieza suelta.")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = PiezaSueltaForm()

    return render(
        request,
        "taller/desarme/pieza_suelta_form.html",
        {"form": form, "empresa": empresa, "titulo": "Agregar pieza suelta"},
    )


@login_required
@role_required("Owner", "Admin")
def editar_pieza(request, pk):
    """Edición de pieza de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    pieza = get_object_or_404(PiezaDesarme, pk=pk, empresa=empresa)

    if request.method == "POST":
        form = PiezaDesarmeForm(request.POST, instance=pieza, empresa=empresa)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Pieza actualizada.")
                if pieza.vehiculo_desarme_id:
                    return redirect(
                        _desarme_url(request, f"vehiculos/{pieza.vehiculo_desarme_id}/inventario-inteligente/")
                    )
                return redirect(_desarme_url(request, "piezas/"))
            except Exception as e:
                log.exception("Error actualizando pieza de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = PiezaDesarmeForm(instance=pieza, empresa=empresa)

    return render(
        request,
        "taller/desarme/pieza_form.html",
        {"form": form, "pieza": pieza, "empresa": empresa, "titulo": "Editar pieza de desarme"},
    )


@login_required
@require_POST
def iniciar_venta_desde_inventario(request, pk):
    """
    Inicia una venta desde el inventario de desarme, guardando un prefill de repuestos
    en sesión y redirigiendo al formulario moderno de documentos.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    pieza_ids = request.POST.getlist("pieza_ids") or []
    pieza_ids_int = []
    for raw_id in pieza_ids:
        try:
            pieza_ids_int.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    if not pieza_ids_int:
        messages.warning(request, "No se seleccionaron piezas válidas para la venta.")
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    valid_estados = {ESTADO_DISPONIBLE, ESTADO_RESERVADA}
    piezas_qs = PiezaDesarme.objects.filter(
        pk__in=pieza_ids_int,
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        activo=True,
        estado_pieza__in=valid_estados,
        cantidad__gt=0,
    ).prefetch_related("names", "company_labels")

    piezas_by_id = {p.pk: p for p in piezas_qs}
    repuestos_prefill = []
    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]

    for pieza_id in pieza_ids_int:
        pieza = piezas_by_id.get(pieza_id)
        if not pieza:
            continue

        raw_cantidad = request.POST.get(f"cantidad_{pieza_id}", "").strip() or "1"
        try:
            cantidad_solicitada = int(raw_cantidad)
        except (TypeError, ValueError):
            cantidad_solicitada = 0

        if cantidad_solicitada <= 0:
            continue

        if cantidad_solicitada > pieza.cantidad:
            cantidad_solicitada = pieza.cantidad

        try:
            precio_venta = float(pieza.precio_venta_sugerido or 0)
        except (TypeError, ValueError):
            precio_venta = 0.0

        try:
            costo_linea = float(pieza.costo_asignado or 0)
        except (TypeError, ValueError):
            costo_linea = 0.0
        repuestos_prefill.append(
            {
                "codigo": pieza.codigo or "",
                "nombre": pieza.get_display_label(empresa=empresa, language=lang)
                or pieza.nombre
                or "",
                "cantidad": cantidad_solicitada,
                "precio": precio_venta,
                "descuento": 0,
                "origen_repuesto": ORIGEN_DESARME,
                "pieza_desarme_id": pieza.id,
                "costo_linea": costo_linea,
                "vehiculo_origen_label": str(pieza.vehiculo_desarme),
            }
        )

    if not repuestos_prefill:
        messages.warning(
            request,
            "Las piezas seleccionadas no son vendibles o no tienen stock disponible.",
        )
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    request.session["desarme_repuestos_prefill"] = repuestos_prefill
    request.session["desarme_origen_label"] = str(vehiculo)

    try:
        doc_url = _reverse_with_request(request, "documento_crear")
    except Exception:
        # Fallback conservador al path clásico manteniendo prefijo país/idioma
        path = (request.path or "").lower()
        if path.startswith("/us/"):
            doc_url = "/us/en/documentos/form/"
        else:
            doc_url = "/cl/es/documentos/form/"

    return redirect(doc_url)


@login_required
@require_POST
def api_pieza_actualizar_estado(request, pk):
    """Actualiza estado de pieza vía AJAX. Body: {estado: 'DISPONIBLE'|'DANADA'|'FALTANTE'}"""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)

    pieza = get_object_or_404(PiezaDesarme, pk=pk, empresa=empresa)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    estado = (data.get("estado") or "").strip().upper()
    validos = {ESTADO_DISPONIBLE, ESTADO_DANADA, ESTADO_FALTANTE, ESTADO_RESERVADA, ESTADO_SCRAP}
    if estado not in validos:
        return JsonResponse({"success": False, "error": "Estado inválido"}, status=400)

    pieza.estado_pieza = estado
    pieza.save(update_fields=["estado_pieza"])
    return JsonResponse({"success": True, "estado": estado})


@login_required
@require_POST
def api_pieza_actualizar_precio(request, pk):
    """Actualiza precio de pieza vía AJAX. Body: {precio: 85000}"""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)

    pieza = get_object_or_404(PiezaDesarme, pk=pk, empresa=empresa)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    try:
        precio = Decimal(str(data.get("precio", 0)))
        if precio < 0:
            raise ValueError("Precio negativo")
    except (ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Precio inválido"}, status=400)

    pieza.precio_venta_sugerido = precio
    pieza.save(update_fields=["precio_venta_sugerido"])
    return JsonResponse({"success": True, "precio": str(precio)})


@login_required
@require_POST
def api_pieza_label_empresa_guardar(request, pk):
    """
    Crea o actualiza el nombre visible por empresa/idioma para una pieza de desarme.
    Body JSON: { "language": "en", "label": "Valve Cover", "aliases": ["rocker cover"] }
    Solo piezas de la empresa del usuario. Upsert sobre PiezaDesarmeCompanyLabel.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)

    pieza = get_object_or_404(PiezaDesarme, pk=pk, empresa=empresa)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    language = (data.get("language") or "es").strip()[:2].lower()
    if language not in ("es", "en", "pt"):
        language = "es"
    label = (data.get("label") or "").strip()[:255]
    if not label:
        return JsonResponse({"success": False, "error": "label es obligatorio"}, status=400)

    raw_aliases = data.get("aliases")
    if not isinstance(raw_aliases, list):
        raw_aliases = []
    aliases = [str(a).strip() for a in raw_aliases if a is not None and str(a).strip()][:50]

    obj, created = PiezaDesarmeCompanyLabel.objects.update_or_create(
        empresa=empresa,
        pieza_desarme=pieza,
        language=language,
        defaults={"label": label, "aliases": aliases, "is_preferred": True},
    )
    return JsonResponse(
        {
            "success": True,
            "label": obj.label,
            "language": obj.language,
            "aliases": obj.aliases,
        }
    )


@login_required
@role_required("Owner", "Admin")
@require_POST
def api_piezas_bulk_estado(request):
    """
    Actualiza estado de varias piezas en una sola petición.
    Body: { "ids": [1, 2, 3], "estado": "DISPONIBLE"|"DANADA"|"FALTANTE" }
    Solo actualiza piezas de la empresa del usuario.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    ids = data.get("ids")
    if not isinstance(ids, list):
        return JsonResponse({"success": False, "error": "ids debe ser una lista"}, status=400)
    ids = [int(x) for x in ids if str(x).isdigit()][:100]  # límite 100 por petición
    if not ids:
        return JsonResponse({"success": False, "error": "No hay IDs válidos"}, status=400)

    estado = (data.get("estado") or "").strip().upper()
    validos = {ESTADO_DISPONIBLE, ESTADO_DANADA, ESTADO_FALTANTE, ESTADO_RESERVADA, ESTADO_SCRAP}
    if estado not in validos:
        return JsonResponse({"success": False, "error": "Estado inválido"}, status=400)

    updated = PiezaDesarme.objects.filter(pk__in=ids, empresa=empresa).update(estado_pieza=estado)
    return JsonResponse({"success": True, "updated": updated, "estado": estado})


@login_required
@role_required("Owner", "Admin")
@require_POST
def api_piezas_bulk_precio(request):
    """
    Dos modos de operación:

    Modo A — ajuste porcentual (comportamiento original, intacto):
        Body: { "ids": [1, 2, 3], "factor": 1.1 }
        Multiplica precio_venta_sugerido × factor en las piezas indicadas.

    Modo B — precio absoluto por filtro de zona/texto:
        Body: {
            "precio_absoluto": 15000,
            "zona": "motor",          # opcional, vacío = no filtrar por zona
            "texto_filtro": "tambor", # opcional, case-insensitive sobre nombre
            "solo_contar": true       # si true, devuelve conteo sin modificar nada
        }
        Exige al menos uno de zona o texto_filtro (nunca actualiza todo el
        inventario sin filtro). Aplica solo a piezas activas de la empresa.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    # ── Modo A: ajuste porcentual (ids + factor) ──────────────────────────────
    if "ids" in data:
        ids = data.get("ids")
        if not isinstance(ids, list):
            return JsonResponse({"success": False, "error": "ids debe ser una lista"}, status=400)
        ids = [int(x) for x in ids if str(x).isdigit()][:100]
        if not ids:
            return JsonResponse({"success": False, "error": "No hay IDs válidos"}, status=400)

        try:
            factor = Decimal(str(data.get("factor", 1)))
            if factor <= 0 or factor > 5:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"success": False, "error": "Factor inválido (0 < factor ≤ 5)"}, status=400)

        piezas = list(PiezaDesarme.objects.filter(pk__in=ids, empresa=empresa))
        updated = 0
        for p in piezas:
            if p.precio_venta_sugerido and p.precio_venta_sugerido > 0:
                nuevo = (p.precio_venta_sugerido * factor).quantize(Decimal("1"))
                p.precio_venta_sugerido = max(nuevo, Decimal("0"))
                p.save(update_fields=["precio_venta_sugerido"])
                updated += 1
        return JsonResponse({"success": True, "updated": updated, "factor": str(factor)})

    # ── Modo B: precio absoluto por zona / texto ──────────────────────────────
    if "precio_absoluto" not in data:
        return JsonResponse(
            {"success": False, "error": "Se requiere 'ids'+'factor' o 'precio_absoluto'"},
            status=400,
        )

    try:
        precio_absoluto = Decimal(str(data["precio_absoluto"])).quantize(Decimal("1"))
        if precio_absoluto < 0:
            raise ValueError
    except (ValueError, TypeError, Exception):
        return JsonResponse({"success": False, "error": "precio_absoluto debe ser un número ≥ 0"}, status=400)

    zona = (data.get("zona") or "").strip()
    texto_filtro = (data.get("texto_filtro") or "").strip()
    solo_contar = bool(data.get("solo_contar", False))

    # Seguridad: exige al menos un filtro real
    if not zona and not texto_filtro:
        return JsonResponse(
            {"success": False, "error": "Debes indicar al menos 'zona' o 'texto_filtro' para aplicar un precio absoluto"},
            status=400,
        )

    qs = PiezaDesarme.objects.filter(empresa=empresa, activo=True)
    if zona:
        qs = qs.filter(zona__iexact=zona)
    if texto_filtro:
        qs = qs.filter(nombre__icontains=texto_filtro)

    if solo_contar:
        return JsonResponse({"success": True, "count": qs.count()})

    updated = qs.update(precio_venta_sugerido=precio_absoluto)
    return JsonResponse({"success": True, "updated": updated, "precio_absoluto": str(precio_absoluto)})


@login_required
@require_POST
def iniciar_venta_desde_lista(request):
    """
    Inicia una venta desde la lista de repuestos (carrito multi-vehículo),
    guardando un prefill de repuestos en sesión y redirigiendo al formulario de documentos.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")
    pieza_ids = request.POST.getlist("pieza_ids") or []
    pieza_ids_int = []
    for raw_id in pieza_ids:
        try:
            pieza_ids_int.append(int(raw_id))
        except (TypeError, ValueError):
            continue
    if not pieza_ids_int:
        messages.warning(request, "No se seleccionaron repuestos para la venta.")
        return redirect(_desarme_url(request, "piezas/"))
    valid_estados = {ESTADO_DISPONIBLE, ESTADO_RESERVADA}
    piezas_qs = PiezaDesarme.objects.filter(
        pk__in=pieza_ids_int,
        empresa=empresa,
        activo=True,
        estado_pieza__in=valid_estados,
        cantidad__gt=0,
    ).prefetch_related("names", "company_labels")
    piezas_by_id = {p.pk: p for p in piezas_qs}
    repuestos_prefill = []
    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]
    for pieza_id in pieza_ids_int:
        pieza = piezas_by_id.get(pieza_id)
        if not pieza:
            continue
        raw_cantidad = request.POST.get(f"cantidad_{pieza_id}", "").strip() or "1"
        try:
            cantidad_solicitada = int(raw_cantidad)
        except (TypeError, ValueError):
            cantidad_solicitada = 0
        if cantidad_solicitada <= 0:
            continue
        if cantidad_solicitada > pieza.cantidad:
            cantidad_solicitada = pieza.cantidad
        try:
            precio_venta = float(pieza.precio_venta_sugerido or 0)
        except (TypeError, ValueError):
            precio_venta = 0.0
        try:
            costo_linea = float(pieza.costo_asignado or 0)
        except (TypeError, ValueError):
            costo_linea = 0.0
        repuestos_prefill.append(
            {
                "codigo": pieza.codigo or "",
                "nombre": pieza.get_display_label(empresa=empresa, language=lang)
                or pieza.nombre
                or "",
                "cantidad": cantidad_solicitada,
                "precio": precio_venta,
                "descuento": 0,
                "origen_repuesto": ORIGEN_DESARME,
                "pieza_desarme_id": pieza.id,
                "costo_linea": costo_linea,
                "vehiculo_origen_label": str(pieza.vehiculo_desarme),
            }
        )
    if not repuestos_prefill:
        messages.warning(request, "Las piezas seleccionadas no son vendibles o no tienen stock disponible.")
        return redirect(_desarme_url(request, "piezas/"))
    request.session["desarme_repuestos_prefill"] = repuestos_prefill
    request.session["desarme_origen_label"] = "Lista de repuestos"
    try:
        doc_url = _reverse_with_request(request, "documento_crear")
    except Exception:
        path = (request.path or "").lower()
        if path.startswith("/us/"):
            doc_url = "/us/en/documentos/form/"
        else:
            doc_url = "/cl/es/documentos/form/"
    return redirect(doc_url)


# ── Pantalla fusionada de revisión ───────────────────────────────────────────

@login_required
def revisar_vehiculo(request, pk):
    """
    GET  → pantalla de revisión: sugerencias del catálogo (PENDIENTE/CONFIRMADA/DESCARTADA).
    POST → AJAX JSON con action=confirmar|descartar|reabrir|agregar.
    PiezaDesarme real solo se crea al confirmar; progreso persiste en SugerenciaPiezaDesarme.
    """
    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
    from taller.models.pieza_desarme import CONDICION_CHOICES
    from .services import inicializar_sugerencias

    empresa = _empresa_or_redirect(request)
    if not empresa:
        if request.method == "POST":
            return JsonResponse({"success": False, "error": "Sin empresa"}, status=403)
        return redirect("/")

    vehiculo = VehiculoDesarme.objects.filter(pk=pk, empresa=empresa).first()
    if vehiculo is None:
        vehiculo_legacy = Vehiculo.objects.filter(
            pk=pk, empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME
        ).first()
        if vehiculo_legacy is None:
            return get_object_or_404(VehiculoDesarme, pk=pk, empresa=empresa)
        vehiculo = _ensure_vehiculo_desarme(vehiculo_legacy, empresa)

    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

        action = (data.get("action") or "").strip()
        if action == "confirmar":
            return _revisar_confirmar(data, vehiculo, empresa)
        if action == "descartar":
            return _revisar_descartar(data, vehiculo, empresa)
        if action == "reabrir":
            return _revisar_reabrir(data, vehiculo, empresa)
        if action == "agregar":
            return _revisar_agregar(data, vehiculo, empresa)
        if action == "finalizar_sesion":
            return _revisar_finalizar_sesion(data, vehiculo, empresa, request.user, request)
        return JsonResponse({"success": False, "error": "Acción desconocida"}, status=400)

    # GET ──────────────────────────────────────────────────────────────────────
    sugerencias_qs = (
        SugerenciaPiezaDesarme.objects
        .filter(empresa=empresa, vehiculo_desarme=vehiculo)
        .select_related("pieza_creada")
    )
    if not sugerencias_qs.exists():
        # Auto-inicializar solo si el vehículo aún no tiene piezas
        if not PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).exists():
            inicializar_sugerencias(vehiculo, empresa)
            sugerencias_qs = (
                SugerenciaPiezaDesarme.objects
                .filter(empresa=empresa, vehiculo_desarme=vehiculo)
                .select_related("pieza_creada")
            )

    sugerencias = list(sugerencias_qs.order_by("zona", "codigo"))

    from .catalogo_operativo import get_zonas_orden_desarme
    sug_por_zona: dict = {}
    for s in sugerencias:
        sug_por_zona.setdefault(s.zona or "Otros", []).append(s)

    zonas_orden = [z for z in get_zonas_orden_desarme(empresa) if z in sug_por_zona]
    zonas_orden.extend(z for z in sorted(sug_por_zona) if z not in zonas_orden)
    zonas_con_sugerencias = [(z, sug_por_zona[z]) for z in zonas_orden]

    total      = len(sugerencias)
    pendientes = sum(1 for s in sugerencias if s.estado == SugerenciaPiezaDesarme.PENDIENTE)
    confirmadas = sum(1 for s in sugerencias if s.estado == SugerenciaPiezaDesarme.CONFIRMADA)
    descartadas = sum(1 for s in sugerencias if s.estado == SugerenciaPiezaDesarme.DESCARTADA)
    pct = round((confirmadas + descartadas) / total * 100) if total else 0

    from taller.desarme.selectors.sesion_despiece import get_sesion_despiece
    sesion = get_sesion_despiece(vehiculo.pk, empresa)

    # Valor estimado de las piezas confirmadas (sum de precio_sugerido)
    from django.db.models import Sum as _Sum
    valor_estimado = (
        SugerenciaPiezaDesarme.objects.filter(
            empresa=empresa,
            vehiculo_desarme=vehiculo,
            estado=SugerenciaPiezaDesarme.CONFIRMADA,
        ).aggregate(total=_Sum("precio_sugerido"))["total"]
        or Decimal("0")
    )

    return render(request, "taller/desarme/revisar_vehiculo.html", {
        "vehiculo": vehiculo,
        "empresa": empresa,
        "zonas_con_sugerencias": zonas_con_sugerencias,
        "sesion": sesion,
        "total": total,
        "pendientes": pendientes,
        "confirmadas": confirmadas,
        "descartadas": descartadas,
        "pct_completado": pct,
        "valor_estimado": valor_estimado,
        "condicion_choices": CONDICION_CHOICES,
        "empresa_moneda": empresa.formato_moneda,
        "PENDIENTE":  SugerenciaPiezaDesarme.PENDIENTE,
        "CONFIRMADA": SugerenciaPiezaDesarme.CONFIRMADA,
        "DESCARTADA": SugerenciaPiezaDesarme.DESCARTADA,
    })


def _revisar_confirmar(data, vehiculo, empresa):
    """Confirma una sugerencia — guarda precio y condición pero NO crea PiezaDesarme todavía."""
    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
    from taller.models.pieza_desarme import CONDICION_BUENA, CONDICION_REGULAR

    sug_id = data.get("sugerencia_id")
    if not sug_id:
        return JsonResponse({"success": False, "error": "sugerencia_id requerido"}, status=400)
    sug = get_object_or_404(
        SugerenciaPiezaDesarme, pk=sug_id, empresa=empresa, vehiculo_desarme=vehiculo
    )

    # estado_visual cycling: verde=BUENA, amarillo=REGULAR
    estado_visual = (data.get("estado_visual") or "verde").strip()
    condicion = CONDICION_REGULAR if estado_visual == "amarillo" else CONDICION_BUENA

    try:
        precio = Decimal(str(data["precio"])) if "precio" in data and data["precio"] not in (None, "") else sug.precio_sugerido
    except Exception:
        precio = sug.precio_sugerido

    with transaction.atomic():
        sug.estado = SugerenciaPiezaDesarme.CONFIRMADA
        sug.precio_sugerido = precio
        sug.condicion_sugerida = condicion
        sug.save(update_fields=["estado", "precio_sugerido", "condicion_sugerida", "updated_at"])

        # Backward compat: if pieza_creada already exists (legacy data), update its price/condition
        if sug.pieza_creada_id:
            PiezaDesarme.objects.filter(pk=sug.pieza_creada_id).update(
                precio_venta_sugerido=precio,
                condicion=condicion,
            )

    from django.db.models import Sum as _Sum
    valor_acumulado = (
        SugerenciaPiezaDesarme.objects.filter(
            empresa=empresa, vehiculo_desarme=vehiculo, estado=SugerenciaPiezaDesarme.CONFIRMADA
        ).aggregate(total=_Sum("precio_sugerido"))["total"]
        or Decimal("0")
    )
    pendientes = SugerenciaPiezaDesarme.objects.filter(
        empresa=empresa, vehiculo_desarme=vehiculo, estado=SugerenciaPiezaDesarme.PENDIENTE
    ).count()

    return JsonResponse({
        "success": True,
        "estado_visual": estado_visual,
        "precio": float(precio or 0),
        "valor_acumulado": float(valor_acumulado),
        "pendientes": pendientes,
    })


def _revisar_descartar(data, vehiculo, empresa):
    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme

    sug_id = data.get("sugerencia_id")
    if not sug_id:
        return JsonResponse({"success": False, "error": "sugerencia_id requerido"}, status=400)
    sug = get_object_or_404(
        SugerenciaPiezaDesarme, pk=sug_id, empresa=empresa, vehiculo_desarme=vehiculo
    )
    sug.estado = SugerenciaPiezaDesarme.DESCARTADA
    sug.save(update_fields=["estado", "updated_at"])

    pendientes = SugerenciaPiezaDesarme.objects.filter(
        empresa=empresa, vehiculo_desarme=vehiculo, estado=SugerenciaPiezaDesarme.PENDIENTE
    ).count()
    return JsonResponse({"success": True, "pendientes": pendientes})


def _revisar_reabrir(data, vehiculo, empresa):
    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
    from taller.desarme.services import puede_eliminar_pieza

    sug_id = data.get("sugerencia_id")
    if not sug_id:
        return JsonResponse({"success": False, "error": "sugerencia_id requerido"}, status=400)
    sug = get_object_or_404(
        SugerenciaPiezaDesarme, pk=sug_id, empresa=empresa, vehiculo_desarme=vehiculo
    )
    with transaction.atomic():
        if sug.pieza_creada_id:
            pieza = sug.pieza_creada
            can_delete, reason = puede_eliminar_pieza(pieza)
            if not can_delete:
                return JsonResponse({"success": False, "error": reason}, status=400)
            pieza.delete()
            sug.pieza_creada = None
        sug.estado = SugerenciaPiezaDesarme.PENDIENTE
        sug.precio_sugerido = None
        sug.condicion_sugerida = None
        sug.save(update_fields=["estado", "pieza_creada", "precio_sugerido", "condicion_sugerida", "updated_at"])

    from django.db.models import Sum as _Sum
    valor_acumulado = (
        SugerenciaPiezaDesarme.objects.filter(
            empresa=empresa, vehiculo_desarme=vehiculo, estado=SugerenciaPiezaDesarme.CONFIRMADA
        ).aggregate(total=_Sum("precio_sugerido"))["total"]
        or Decimal("0")
    )
    pendientes = SugerenciaPiezaDesarme.objects.filter(
        empresa=empresa, vehiculo_desarme=vehiculo, estado=SugerenciaPiezaDesarme.PENDIENTE
    ).count()
    return JsonResponse({
        "success": True,
        "pendientes": pendientes,
        "valor_acumulado": float(valor_acumulado),
    })


def _revisar_agregar(data, vehiculo, empresa):
    """Agrega pieza extra fuera del catálogo — crea solo SugerenciaPiezaDesarme (CONFIRMADA).
    PiezaDesarme se crea en bulk al llamar finalizar_sesion."""
    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
    from taller.models.pieza_desarme import CONDICION_BUENA

    codigo = (data.get("codigo") or "").strip()
    nombre = (data.get("nombre") or "").strip()
    zona   = (data.get("zona") or "Otros").strip()
    if not codigo or not nombre:
        return JsonResponse({"success": False, "error": "código y nombre son requeridos"}, status=400)

    condicion = (data.get("condicion") or CONDICION_BUENA).strip()
    try:
        precio = Decimal(str(data.get("precio") or 0))
    except Exception:
        precio = Decimal("0")

    try:
        sug = SugerenciaPiezaDesarme.objects.create(
            empresa=empresa,
            vehiculo_desarme=vehiculo,
            codigo=codigo,
            nombre=nombre,
            zona=zona,
            precio_sugerido=precio,
            condicion_sugerida=condicion,
            estado=SugerenciaPiezaDesarme.CONFIRMADA,
        )
    except IntegrityError:
        return JsonResponse({
            "success": False,
            "error": f"Ya existe una pieza con código '{codigo}' en este vehículo",
        }, status=400)

    from django.db.models import Sum as _Sum
    valor_acumulado = (
        SugerenciaPiezaDesarme.objects.filter(
            empresa=empresa, vehiculo_desarme=vehiculo, estado=SugerenciaPiezaDesarme.CONFIRMADA
        ).aggregate(total=_Sum("precio_sugerido"))["total"]
        or Decimal("0")
    )

    return JsonResponse({
        "success": True,
        "sugerencia_id": sug.pk,
        "nombre": sug.nombre,
        "codigo": sug.codigo,
        "zona": sug.zona,
        "valor_acumulado": float(valor_acumulado),
    })


def _revisar_finalizar_sesion(data, vehiculo, empresa, user, request):
    """
    Cierra la sesión de despiece:
    - Crea PiezaDesarme en bulk para cada SugerenciaPiezaDesarme CONFIRMADA sin pieza_creada.
    - Escribe VehiculoDesarmeEvent(tipo=SESION_DESPIECE_FINALIZADA).
    - Avanza vehiculo.estado_operativo a EN_PROCESAMIENTO.
    """
    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
    from taller.models.vehiculo_desarme_event import VehiculoDesarmeEvent, TipoEventoDesarme
    from taller.models.vehiculo_desarme import EstadoOperativo
    from taller.models.pieza_desarme import CONDICION_BUENA

    with transaction.atomic():
        confirmadas = list(
            SugerenciaPiezaDesarme.objects
            .select_for_update()
            .filter(
                empresa=empresa,
                vehiculo_desarme=vehiculo,
                estado=SugerenciaPiezaDesarme.CONFIRMADA,
                pieza_creada__isnull=True,
            )
            .order_by("id")
        )

        if not confirmadas:
            return JsonResponse(
                {"success": False, "error": "No hay piezas confirmadas pendientes de crear"},
                status=400,
            )

        piezas_nuevas = [
            PiezaDesarme(
                empresa=empresa,
                vehiculo_desarme=vehiculo,
                codigo=sug.codigo,
                nombre=sug.nombre,
                zona=sug.zona or "",
                precio_venta_sugerido=sug.precio_sugerido,
                condicion=sug.condicion_sugerida or CONDICION_BUENA,
                estado_pieza=ESTADO_DISPONIBLE,
                activo=True,
                revisado=True,
                fecha_revision=timezone.now(),
                cantidad=1,
            )
            for sug in confirmadas
        ]
        PiezaDesarme.objects.bulk_create(piezas_nuevas)

        # Link each sugerencia to its newly created pieza (bulk_create sets PKs in Django 4.1+)
        for sug, pieza in zip(confirmadas, piezas_nuevas):
            sug.pieza_creada = pieza
            sug.save(update_fields=["pieza_creada", "updated_at"])

        VehiculoDesarmeEvent.objects.create(
            empresa=empresa,
            vehiculo=vehiculo,
            tipo=TipoEventoDesarme.SESION_DESPIECE_FINALIZADA,
            metadata={"piezas_creadas": len(piezas_nuevas)},
            created_by=user,
        )

        from taller.models.vehiculo_desarme import VehiculoDesarme as _VD
        _VD.objects.filter(pk=vehiculo.pk).update(
            estado_operativo=EstadoOperativo.EN_PROCESAMIENTO,
        )

    redirect_url = _desarme_url(request, f"vehiculos/{vehiculo.pk}/")
    return JsonResponse({
        "success": True,
        "piezas_creadas": len(piezas_nuevas),
        "redirect_url": redirect_url,
    })


@login_required
@role_required("Owner", "Admin", "Vendedor")
def avisar_owner_pieza(request, pk):
    """Genera redirect a wa.me para que Vendedor notifique al owner sobre una pieza."""
    pieza = get_object_or_404(PiezaDesarme, pk=pk)
    empresa = get_user_empresa_safe(request.user)

    if not empresa or pieza.empresa_id != empresa.pk:
        messages.error(request, "No tienes acceso a esta pieza.")
        return redirect(_desarme_url(request, "piezas/"))

    raw_phone = (pieza.empresa.telefono or "").strip()
    owner_phone = re.sub(r"\D", "", raw_phone)
    if not owner_phone:
        messages.error(
            request,
            "El owner no tiene teléfono registrado. Agréguelo en Configuración.",
        )
        return redirect(_desarme_url(request, "piezas/"))

    precio_val = pieza.precio_venta_sugerido
    if precio_val is None:
        precio_str = "No especificado"
    else:
        fmt = pieza.empresa.formato_moneda
        simbolo = fmt["simbolo"]
        if fmt["decimales"] == 2:
            precio_str = f"{simbolo}{precio_val:,.2f}"
        else:
            miles = f"{int(precio_val):,}".replace(",", ".")
            precio_str = f"{simbolo}{miles}"

    inventario_url = request.build_absolute_uri(
        _desarme_url(request, f"vehiculos/{pieza.vehiculo_desarme_id}/inventario-inteligente/")
    )
    vendedor_nombre = request.user.get_full_name() or request.user.username

    mensaje = (
        f"Hola, quiero vender esta pieza:\n\n"
        f"📌 Código: {pieza.codigo}\n"
        f"📝 Nombre: {pieza.nombre}\n"
        f"💰 Precio sugerido: {precio_str}\n"
        f"🔗 Ver inventario: {inventario_url}\n\n"
        f"Contacto: {vendedor_nombre} / {request.user.email}"
    )

    wa_url = f"https://wa.me/{owner_phone}?{urlencode({'text': mensaje})}"
    return redirect(wa_url)


# ── Interchange manual de piezas ───────────────────────────────────────────────

@login_required
def lista_interchange(request):
    """Lista los patrones de interchange registrados por la empresa."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    from taller.models.interchange_pieza import InterchangePieza

    qs = InterchangePieza.objects.filter(empresa=empresa).order_by("codigo_pieza", "-veces_confirmado")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(codigo_pieza__icontains=q)
            | Q(nombre_pieza__icontains=q)
            | Q(marca_origen__icontains=q)
            | Q(modelo_origen__icontains=q)
            | Q(marca_compatible__icontains=q)
            | Q(modelo_compatible__icontains=q)
        )

    return render(request, "taller/desarme/lista_interchange.html", {
        "interchanges": qs,
        "q": q,
    })


@login_required
def crear_interchange(request):
    """
    GET  → formulario.
    POST → upsert: si ya existe la combinación (empresa+pieza+marca/modelo origen+compatible),
           incrementa veces_confirmado; si no existe, crea con veces_confirmado=1.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    from taller.models.interchange_pieza import InterchangePieza
    from .catalogo_operativo import get_catalogo_operativo_desarme

    catalogo = get_catalogo_operativo_desarme(empresa)

    if request.method == "POST":
        codigo_pieza      = request.POST.get("codigo_pieza", "").strip()
        nombre_pieza      = request.POST.get("nombre_pieza", "").strip()
        marca_origen      = request.POST.get("marca_origen", "").strip().upper()
        modelo_origen     = request.POST.get("modelo_origen", "").strip().upper()
        marca_compatible  = request.POST.get("marca_compatible", "").strip().upper()
        modelo_compatible = request.POST.get("modelo_compatible", "").strip().upper()
        notas             = request.POST.get("notas", "").strip()

        # Años — validación básica
        try:
            anio_origen_desde    = int(request.POST.get("anio_origen_desde", 0))
            anio_origen_hasta    = int(request.POST.get("anio_origen_hasta", 0))
            anio_compatible_desde = int(request.POST.get("anio_compatible_desde", 0))
            anio_compatible_hasta = int(request.POST.get("anio_compatible_hasta", 0))
        except (ValueError, TypeError):
            messages.error(request, "Los años deben ser números válidos.")
            return render(request, "taller/desarme/crear_interchange.html", {
                "catalogo": catalogo, "post": request.POST,
            })

        campos_requeridos = [codigo_pieza, marca_origen, modelo_origen, marca_compatible, modelo_compatible]
        if not all(campos_requeridos) or not all([anio_origen_desde, anio_origen_hasta, anio_compatible_desde, anio_compatible_hasta]):
            messages.error(request, "Todos los campos marcados con * son obligatorios.")
            return render(request, "taller/desarme/crear_interchange.html", {
                "catalogo": catalogo, "post": request.POST,
            })

        # Si nombre_pieza vacío, tomarlo del catálogo
        if not nombre_pieza:
            for item in catalogo:
                if item["codigo"] == codigo_pieza:
                    nombre_pieza = item["nombre"]
                    break

        # Upsert: el constraint unique NO incluye años, así que buscamos por los 5 campos del constraint
        existing = InterchangePieza.objects.filter(
            empresa=empresa,
            codigo_pieza=codigo_pieza,
            marca_origen=marca_origen,
            modelo_origen=modelo_origen,
            marca_compatible=marca_compatible,
            modelo_compatible=modelo_compatible,
        ).first()

        if existing:
            InterchangePieza.objects.filter(pk=existing.pk).update(
                veces_confirmado=F("veces_confirmado") + 1
            )
            existing.refresh_from_db(fields=["veces_confirmado"])
            messages.success(
                request,
                f"Compatibilidad ya conocida — confirmada ×{existing.veces_confirmado} veces.",
            )
        else:
            InterchangePieza.objects.create(
                empresa=empresa,
                codigo_pieza=codigo_pieza,
                nombre_pieza=nombre_pieza,
                marca_origen=marca_origen,
                modelo_origen=modelo_origen,
                anio_origen_desde=anio_origen_desde,
                anio_origen_hasta=anio_origen_hasta,
                marca_compatible=marca_compatible,
                modelo_compatible=modelo_compatible,
                anio_compatible_desde=anio_compatible_desde,
                anio_compatible_hasta=anio_compatible_hasta,
                notas=notas,
            )
            messages.success(request, "Interchange registrado correctamente.")

        return redirect(_desarme_url(request, "interchange/"))

    return render(request, "taller/desarme/crear_interchange.html", {
        "catalogo": catalogo,
        "post": {},
    })


@login_required
@require_POST
def eliminar_interchange(request, pk):
    """Elimina un registro de interchange — solo si pertenece a la empresa del usuario."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    from taller.models.interchange_pieza import InterchangePieza

    ix = get_object_or_404(InterchangePieza, pk=pk, empresa=empresa)
    ix.delete()
    messages.success(request, "Registro de interchange eliminado.")
    return redirect(_desarme_url(request, "interchange/"))


@login_required
def reportes_desarme(request):
    """Reportes financieros y de inventario exclusivos del módulo Desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    from taller.services.desarme_kpi_service import (
        kpis_resumen,
        top_piezas,
        top_vehiculos,
        top_marcas,
        top_modelos,
        top_roi_vehiculos,
    )

    kpis = kpis_resumen(empresa)
    return render(
        request,
        "taller/desarme/reportes.html",
        {
            "eg_desarme_dashboard_compact": True,
            "empresa": empresa,
            "kpis": kpis,
            "top_piezas": top_piezas(empresa, limit=10),
            "top_vehiculos": top_vehiculos(empresa, limit=10),
            "top_marcas": top_marcas(empresa, limit=5),
            "top_modelos": top_modelos(empresa, limit=5),
            "top_roi": top_roi_vehiculos(empresa, limit=5),
        },
    )


@login_required
def configurar_catalogo(request):
    """
    Configuración del catálogo de repuestos de la empresa: qué tipos incluir
    en el kiosko y a qué precio de referencia (CatalogoRepuestoEmpresa).
    Editable en cualquier momento — no es una configuración de una sola vez.
    GET: catálogo completo (sin filtrar por vehículo), cruzado con la
    configuración ya guardada (o precio de referencia + incluido=True default).
    POST: guarda/actualiza CatalogoRepuestoEmpresa por cada código.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    from taller.models.catalogo_repuesto_empresa import CatalogoRepuestoEmpresa
    from .catalogo_operativo import get_catalogo_operativo_desarme, get_zonas_orden_desarme

    catalogo = get_catalogo_operativo_desarme(empresa)

    if request.method == "POST":
        with transaction.atomic():
            for item in catalogo:
                codigo = item["codigo"]
                incluido = request.POST.get(f"incluido-{codigo}") == "on"
                precio_raw = (request.POST.get(f"precio-{codigo}") or "").strip()
                precio = None
                if precio_raw:
                    try:
                        precio = Decimal(precio_raw)
                    except Exception:
                        precio = None
                CatalogoRepuestoEmpresa.objects.update_or_create(
                    empresa=empresa,
                    codigo=codigo,
                    defaults={"incluido": incluido, "precio_predeterminado": precio},
                )
        messages.success(request, "Catálogo de repuestos actualizado.")
        return redirect(_desarme_url(request, "catalogo/"))

    # GET ────────────────────────────────────────────────────────────────────
    config_por_codigo = {
        c.codigo: c for c in CatalogoRepuestoEmpresa.objects.filter(empresa=empresa)
    }
    por_zona: dict = {}
    for item in catalogo:
        cfg = config_por_codigo.get(item["codigo"])
        incluido = cfg.incluido if cfg is not None else True
        if cfg is not None and cfg.precio_predeterminado is not None:
            precio = cfg.precio_predeterminado
        else:
            precio = item["precio_base"]
        # str() de Decimal es locale-independiente (punto decimal siempre) —
        # necesario porque {{ precio }} directo en template usa coma decimal
        # con LANGUAGE_CODE=es, lo que invalida el value="" de <input type="number">.
        precio_str = str(precio) if precio is not None else ""
        por_zona.setdefault(item["zona"], []).append({
            "codigo": item["codigo"],
            "nombre": item["nombre"],
            "zona": item["zona"],
            "incluido": incluido,
            "precio": precio_str,
        })

    zonas_orden = [z for z in get_zonas_orden_desarme(empresa) if z in por_zona]
    zonas_orden.extend(z for z in sorted(por_zona) if z not in zonas_orden)
    zonas_con_items = [(z, por_zona[z]) for z in zonas_orden]

    return render(
        request,
        "taller/desarme/configurar_catalogo.html",
        {
            "eg_desarme_dashboard_compact": True,
            "empresa": empresa,
            "zonas_con_items": zonas_con_items,
            "total_items": len(catalogo),
            "empresa_moneda": empresa.formato_moneda,
        },
    )
