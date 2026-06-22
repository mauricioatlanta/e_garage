# Vistas del módulo Desarme: vehículos tipo DESARME y piezas (solo empresa, tipo_uso=DESARME)

import json
import logging
import re
from decimal import Decimal
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
from taller.models.vehiculos import Vehiculo
from taller.models.inspeccion_ingreso import DanoInspeccion, InspeccionIngreso
from taller.models.vendedor_desarme import VendedorDesarme
from taller.documentos.views_migrated import _reverse_with_request
from .forms import PiezaDesarmeForm, PiezaSueltaForm, VehiculoDesarmeForm
from .services import generar_inventario_vehiculo
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

    base_qs = Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)
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
    ultimas_repuestos = piezas_qs.select_related("vehiculo").filter(activo=True).order_by("-id")[:5]

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
            pieza_desarme__vehiculo_id=OuterRef("pk"),
        )
        .values("pieza_desarme__vehiculo_id")
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
        Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)
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

    estado = request.GET.get("estado", "").strip()
    if estado:
        qs = qs.filter(estado_desarme=estado)

    estados = (
        Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)
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
            vehiculo=vehiculo,
            empresa=empresa,
            codigo__in=codigos_a_resetear,
            estado_pieza__in=[ESTADO_DANADA, ESTADO_FALTANTE],
        ).update(estado_pieza=ESTADO_DISPONIBLE)

    # Aplicar estados nuevos
    for codigo, estado in codigos_nuevo_estado.items():
        PiezaDesarme.objects.filter(
            vehiculo=vehiculo,
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

    inspeccion, _ = InspeccionIngreso.objects.update_or_create(
        vehiculo=vehiculo,
        documento=None,
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
                    vehiculo.tipo_uso = Vehiculo.TIPO_USO_DESARME
                    vehiculo.cliente = None
                    vehiculo.save()
                    _guardar_danos_carroceria(request, vehiculo, empresa)
                messages.success(
                    request, f"Vehículo de desarme {vehiculo.patente or vehiculo.vin} creado."
                )
                try:
                    generar_inventario_vehiculo(vehiculo, empresa)
                except Exception as inv_err:
                    log.exception("Error generando inventario para vehículo pk=%s", vehiculo.pk)
                    messages.warning(request, f"Vehículo guardado, pero falló la generación del inventario: {inv_err}")
                return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/scanner/"))
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
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
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
            pieza_desarme__vehiculo=vehiculo,
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
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
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
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
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
        .select_related("vehiculo", "vehiculo__marca", "vehiculo__modelo")
        .order_by("vehiculo__patente", "codigo")
    )

    q = request.GET.get("q", "").strip()
    if q:
        for term in q.split():
            piezas = piezas.filter(
                Q(codigo__icontains=term)
                | Q(nombre__icontains=term)
                | Q(vehiculo__patente__icontains=term)
                | Q(vehiculo__vin__icontains=term)
                | Q(vehiculo__marca_texto__icontains=term)
                | Q(vehiculo__modelo_texto__icontains=term)
                | Q(vehiculo__marca__nombre__icontains=term)
                | Q(vehiculo__modelo__nombre__icontains=term)
            )

    estado = request.GET.get("estado", "").strip()
    if estado:
        piezas = piezas.filter(estado_pieza=estado)

    vehiculo_id = request.GET.get("vehiculo", "").strip()
    if vehiculo_id:
        piezas = piezas.filter(vehiculo_id=vehiculo_id)

    vehiculos_choices = list(
        Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)
        .order_by("patente", "vin")
        .values_list("id", "patente", "vin")
    )
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
def crear_pieza(request):
    """Alta de pieza de desarme. Opcional ?vehiculo=<id> para pre-seleccionar vehículo."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = None
    vehiculo_id = request.GET.get("vehiculo")
    if vehiculo_id:
        vehiculo = Vehiculo.objects.filter(
            pk=vehiculo_id,
            empresa=empresa,
            tipo_uso=Vehiculo.TIPO_USO_DESARME,
        ).first()

    if request.method == "POST":
        form = PiezaDesarmeForm(request.POST, empresa=empresa, vehiculo=vehiculo)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pieza = form.save(commit=False)
                    pieza.empresa = empresa
                    pieza.save()
                messages.success(request, f"Pieza {pieza.codigo} creada.")
                if pieza.vehiculo_id:
                    return redirect(
                        _desarme_url(request, f"vehiculos/{pieza.vehiculo_id}/inventario/")
                    )
                return redirect(_desarme_url(request, "piezas/"))
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
                    vehiculo = Vehiculo.objects.create(
                        empresa=empresa,
                        tipo_uso=Vehiculo.TIPO_USO_DESARME,
                        es_placeholder=True,
                        patente=patente_sintetica,
                        marca_texto=marca or None,
                        modelo_texto=modelo or None,
                        anio=anio,
                    )
                    codigo = d.get("codigo") or f"SLT-{_uuid.uuid4().hex[:8].upper()}"
                    pieza = PiezaDesarme.objects.create(
                        empresa=empresa,
                        vehiculo=vehiculo,
                        nombre=d["nombre"],
                        codigo=codigo,
                        condicion=d["condicion"],
                        cantidad=d.get("cantidad") or 1,
                        precio_venta_sugerido=d.get("precio_venta_sugerido"),
                        imagen=d.get("imagen"),
                    )
                messages.success(request, f"Pieza «{pieza.nombre}» registrada (origen: {origen_label}).")
                return redirect(_desarme_url(request, "piezas/"))
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
                if pieza.vehiculo_id:
                    return redirect(
                        _desarme_url(request, f"vehiculos/{pieza.vehiculo_id}/inventario/")
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
def inventario_vehiculo(request, pk):
    """Inventario de piezas de un vehículo de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
    )
    piezas = (
        vehiculo.piezas_desarme.filter(activo=True)
        .prefetch_related("names", "company_labels")
        .order_by("zona", "codigo")
    )
    total_piezas = piezas.count()
    disponibles = piezas.filter(estado_pieza=ESTADO_DISPONIBLE).count()
    danadas = piezas.filter(estado_pieza=ESTADO_DANADA).count()
    faltantes = piezas.filter(estado_pieza=ESTADO_FALTANTE).count()
    valor_potencial = sum(
        (p.precio_venta_sugerido or Decimal("0")) * p.cantidad
        for p in piezas
        if p.estado_pieza in (ESTADO_DISPONIBLE, ESTADO_RESERVADA)
    )

    # JSON para Alpine.js (inventario V2 ultra) — nombre visible por empresa/idioma + términos búsqueda
    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]
    items_list = []
    for p in piezas:
        items_list.append(
            {
                "id": p.pk,
                "nombre": p.get_display_label(empresa=empresa, language=lang),
                "search_terms": p.get_search_terms(empresa=empresa, language=lang),
                "sku": p.codigo or "",
                "categoria": p.zona or "General",
                "ubicacion": getattr(p, "ubicacion_fisica", None) or "",
                "precio": float(p.precio_venta_sugerido or 0),
                "stock": p.cantidad,
                "vehiculo": str(vehiculo),
                "imagen": "",
                "vendible": (
                    p.activo
                    and p.cantidad > 0
                    and p.estado_pieza in (ESTADO_DISPONIBLE, ESTADO_RESERVADA)
                ),
            }
        )
    piezas_json = json.dumps(items_list, ensure_ascii=False)

    return render(
        request,
        "taller/desarme/inventario_vehiculo.html",
        {
            "vehiculo": vehiculo,
            "piezas": piezas,
            "repuestos": piezas,
            "empresa": empresa,
            "total_piezas": total_piezas,
            "disponibles": disponibles,
            "danadas": danadas,
            "faltantes": faltantes,
            "valor_potencial": valor_potencial,
            "piezas_json": piezas_json,
            "repuestos_json": piezas_json,
        },
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
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
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
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario/"))

    valid_estados = {ESTADO_DISPONIBLE, ESTADO_RESERVADA}
    piezas_qs = PiezaDesarme.objects.filter(
        pk__in=pieza_ids_int,
        empresa=empresa,
        vehiculo=vehiculo,
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
                "vehiculo_origen_label": str(pieza.vehiculo),
            }
        )

    if not repuestos_prefill:
        messages.warning(
            request,
            "Las piezas seleccionadas no son vendibles o no tienen stock disponible.",
        )
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario/"))

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
@require_GET
def generar_inventario_view(request, pk):
    """Genera inventario desde catálogo y redirige al Scanner. Para vehículos sin piezas."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
    )
    generar_inventario_vehiculo(vehiculo, empresa)
    messages.success(request, "Inventario generado. Revisa el escáner.")
    return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/scanner/"))


@login_required
def scanner_vehiculo(request, pk):
    """
    Escáner de Inventario del vehículo - UI futurista para revisar y editar piezas.
    Aparece automáticamente después de crear el vehículo.
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
    )

    # Compatibilidad defensiva: en algunos deploys el related_name `piezas_desarme`
    # puede no estar disponible (migración parcial / código antiguo). Evitar 500.
    try:
        piezas_qs = vehiculo.piezas_desarme.filter(activo=True).prefetch_related("names", "company_labels")  # type: ignore[attr-defined]
    except Exception:
        piezas_qs = PiezaDesarme.objects.filter(
            vehiculo=vehiculo, activo=True, empresa=empresa
        ).prefetch_related("names", "company_labels")
    piezas = list(piezas_qs.order_by("zona", "codigo"))
    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]
    for p in piezas:
        p.display_nombre = p.get_display_label(empresa=empresa, language=lang)

    # Stats
    total = len(piezas)
    disponibles = sum(1 for p in piezas if p.estado_pieza == ESTADO_DISPONIBLE)
    danadas = sum(1 for p in piezas if p.estado_pieza == ESTADO_DANADA)
    faltantes = sum(1 for p in piezas if p.estado_pieza == ESTADO_FALTANTE)
    sin_precio = sum(
        1
        for p in piezas
        if (p.precio_venta_sugerido is None or p.precio_venta_sugerido == 0)
        and p.estado_pieza in (ESTADO_DISPONIBLE, ESTADO_RESERVADA)
    )
    valor_potencial = sum(
        (p.precio_venta_sugerido or Decimal("0")) * p.cantidad
        for p in piezas
        if p.estado_pieza in (ESTADO_DISPONIBLE, ESTADO_RESERVADA)
    )

    # Agrupar por zona para el blueprint
    piezas_por_zona = {}
    for p in piezas:
        zona = p.zona or "Otros"
        piezas_por_zona.setdefault(zona, []).append(p)

    from .catalogo_operativo import get_zonas_orden_desarme

    zonas_orden = [z for z in get_zonas_orden_desarme(empresa) if z in piezas_por_zona]
    zonas_orden.extend(z for z in sorted(piezas_por_zona) if z not in zonas_orden)
    zonas_con_piezas = [(z, piezas_por_zona[z]) for z in zonas_orden]

    return render(
        request,
        "taller/desarme/scanner_vehiculo.html",
        {
            "vehiculo": vehiculo,
            "piezas": piezas,
            "zonas_con_piezas": zonas_con_piezas,
            "empresa": empresa,
            "total_piezas": total,
            "disponibles": disponibles,
            "danadas": danadas,
            "faltantes": faltantes,
            "sin_precio": sin_precio,
            "valor_potencial": valor_potencial,
        },
    )


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
@require_POST
def api_piezas_bulk_precio(request):
    """
    Reajusta precio de varias piezas por factor.
    Body: { "ids": [1, 2, 3], "factor": 1.1 }  (1.1 = +10%, 0.9 = -10%)
    Solo piezas de la empresa del usuario. Solo aplica a piezas con precio > 0.
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
    ids = [int(x) for x in ids if str(x).isdigit()][:100]
    if not ids:
        return JsonResponse({"success": False, "error": "No hay IDs válidos"}, status=400)

    try:
        factor = Decimal(str(data.get("factor", 1)))
        if factor <= 0 or factor > 5:
            raise ValueError("Factor debe estar entre 0 y 5 (seguridad)")
    except (ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Factor inválido"}, status=400)

    piezas = list(PiezaDesarme.objects.filter(pk__in=ids, empresa=empresa))
    updated = 0
    for p in piezas:
        if p.precio_venta_sugerido and p.precio_venta_sugerido > 0:
            nuevo = (p.precio_venta_sugerido * factor).quantize(Decimal("1"))
            if nuevo < 0:
                nuevo = Decimal("0")
            p.precio_venta_sugerido = nuevo
            p.save(update_fields=["precio_venta_sugerido"])
            updated += 1
    return JsonResponse({"success": True, "updated": updated, "factor": str(factor)})


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
                "vehiculo_origen_label": str(pieza.vehiculo),
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
