from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum, Avg
from django.utils import timezone

from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.pieza_desarme import (
    PiezaDesarme,
    ESTADO_DANADA,
    ESTADO_SCRAP,
    ESTADO_FALTANTE,
    ESTADO_DISPONIBLE,
    ESTADO_RESERVADA,
)
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vendedor_desarme import VendedorDesarme
from .desarme_financial_service import (
    calcular_ingresos_vehiculo,
    calcular_inversion_total_vehiculo,
    calcular_inventario_vivo_vehiculo,
    calcular_ganancia_vehiculo,
    calcular_recuperacion_vehiculo,
    calcular_roi_vehiculo,
)


def kpis_resumen(empresa):
    """Devuelve un dict con KPIs principales listos para mostrar en dashboard."""
    vehs = VehiculoDesarme.objects.filter(empresa=empresa, es_placeholder=False)
    total_inversion = Decimal("0")
    total_ingresos = Decimal("0")
    total_ganancia = Decimal("0")
    for v in vehs:
        total_inversion += calcular_inversion_total_vehiculo(v)
        total_ingresos += calcular_ingresos_vehiculo(v)
        total_ganancia += calcular_ganancia_vehiculo(v)

    roi = Decimal("0")
    if total_inversion > 0:
        roi = (total_ganancia / total_inversion) * Decimal("100")

    return {
        "inversion_total": total_inversion,
        "ingresos": total_ingresos,
        "ganancia": total_ganancia,
        "roi_pct": roi,
    }


def top_piezas(empresa, limit=10, fecha_desde=None, fecha_hasta=None):
    """Top piezas por ingresos generados (DESARME), con filtro de fecha opcional."""
    qs = LineaRepuesto.objects.filter(
        documento__empresa=empresa, documento__estado="EMITIDO", origen_repuesto=ORIGEN_DESARME
    )
    if fecha_desde:
        qs = qs.filter(documento__fecha_emision__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(documento__fecha_emision__lte=fecha_hasta)
    qs = (
        qs.values("pieza_desarme", "pieza_desarme__nombre", "pieza_desarme__codigo")
        .annotate(revenue=Sum(F("precio_unitario") * F("cantidad")), sold=Sum("cantidad"))
        .order_by("-revenue")[:limit]
    )
    result = []
    for r in qs:
        result.append(
            {
                "pieza_id": r.get("pieza_desarme"),
                "codigo": r.get("pieza_desarme__codigo"),
                "nombre": r.get("pieza_desarme__nombre"),
                "revenue": Decimal(r.get("revenue") or 0),
                "sold": int(r.get("sold") or 0),
            }
        )
    return result


def top_vehiculos(empresa, limit=10, fecha_desde=None, fecha_hasta=None):
    """Top vehículos por ingresos agregados de sus piezas (DESARME), con filtro de fecha opcional."""
    qs = LineaRepuesto.objects.filter(
        documento__empresa=empresa, documento__estado="EMITIDO", origen_repuesto=ORIGEN_DESARME
    )
    if fecha_desde:
        qs = qs.filter(documento__fecha_emision__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(documento__fecha_emision__lte=fecha_hasta)
    qs = (
        qs.values("pieza_desarme__vehiculo_desarme_id", "pieza_desarme__vehiculo_desarme__patente")
        .annotate(revenue=Sum(F("precio_unitario") * F("cantidad")), sold=Sum("cantidad"))
        .order_by("-revenue")[:limit]
    )
    result = []
    for r in qs:
        result.append(
            {
                "vehiculo_desarme_id": r.get("pieza_desarme__vehiculo_desarme_id"),
                "patente": r.get("pieza_desarme__vehiculo_desarme__patente"),
                "revenue": Decimal(r.get("revenue") or 0),
                "sold": int(r.get("sold") or 0),
            }
        )
    return result


# --- New analytics functions ---

def dias_stock_promedio(vehiculo):
    """Promedio de días en stock para piezas vendibles del vehículo."""
    today = timezone.now().date()
    piezas = PiezaDesarme.objects.filter(
        vehiculo_desarme_id=vehiculo.id, activo=True, cantidad__gt=0
    ).exclude(fecha_extraccion__isnull=True)
    total_days = 0
    count = 0
    for p in piezas:
        days = (today - p.fecha_extraccion).days if p.fecha_extraccion else 0
        total_days += days
        count += 1
    return (total_days / count) if count else None


def rotacion_piezas(vehiculo):
    """Rotación simple: total vendido / stock medio actual (por vehículo)."""
    sold = LineaRepuesto.objects.filter(
        origen_repuesto=ORIGEN_DESARME, pieza_desarme__vehiculo_desarme_id=vehiculo.id, documento__estado="EMITIDO"
    ).aggregate(total=Sum("cantidad"))["total"] or 0
    stock = PiezaDesarme.objects.filter(vehiculo_desarme_id=vehiculo.id).aggregate(total=Sum("cantidad"))["total"] or 0
    if stock == 0:
        return None
    return float(sold) / float(stock)


def inventario_muerto(vehiculo):
    """Valor contable de piezas en estados no vendibles (DANADA, SCRAP, FALTANTE)."""
    qs = PiezaDesarme.objects.filter(
        vehiculo_desarme_id=vehiculo.id, estado_pieza__in=[ESTADO_DANADA, ESTADO_SCRAP, ESTADO_FALTANTE]
    )
    total = Decimal("0")
    for p in qs:
        qty = int(p.cantidad or 0)
        total += Decimal(p.costo_asignado or 0) * qty
    return total


def potencial_recuperacion(vehiculo):
    """Valor de mercado potencial restante / inversión total."""
    inv = calcular_inversion_total_vehiculo(vehiculo)
    inv_vivo = calcular_inventario_vivo_vehiculo(vehiculo)
    mercado = inv_vivo.get("valor_mercado") or Decimal("0")
    if inv == 0:
        return None
    return (mercado / inv) * Decimal("100")


def health_score(vehiculo):
    """Score 0-100 basado en ROI, dias_recuperacion y inventario muerto/recuperable."""
    roi = calcular_roi_vehiculo(vehiculo)
    dias = dias_stock_promedio(vehiculo) or 0
    inventario_m = inventario_muerto(vehiculo) or Decimal("0")
    inventario_v = calcular_inventario_vivo_vehiculo(vehiculo).get("valor_contable") or Decimal("0")

    # Normalizar ROI: si ROI negative -> 0..50, positive upto 200% -> 50..100
    roi_val = float(roi)
    if roi_val <= 0:
        roi_score = max(0, 50 + (roi_val / 100.0) * 50)
    else:
        roi_score = min(100, 50 + (roi_val / 200.0) * 50)

    # Dias: menos dias -> mejor. Map 0..180 to 100..0
    dias_score = max(0, min(100, 100 - (dias / 180.0) * 100))

    # Inventario muerto ratio
    dead_ratio = (float(inventario_m) / float(inventario_v)) if inventario_v > 0 else 0
    dead_score = max(0, 100 - dead_ratio * 100)

    # Weighted sum
    score = (0.5 * roi_score) + (0.3 * dias_score) + (0.2 * dead_score)
    return round(score, 2)


# Analytics por marca/modelo/ROI

def top_marcas(empresa, limit=10, fecha_desde=None, fecha_hasta=None):
    qs = LineaRepuesto.objects.filter(
        documento__empresa=empresa, documento__estado="EMITIDO", origen_repuesto=ORIGEN_DESARME
    )
    if fecha_desde:
        qs = qs.filter(documento__fecha_emision__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(documento__fecha_emision__lte=fecha_hasta)
    qs = (
        qs.values("pieza_desarme__vehiculo_desarme__marca__nombre")
        .annotate(revenue=Sum(F("precio_unitario") * F("cantidad")))
        .order_by("-revenue")[:limit]
    )
    return [{"marca": r.get("pieza_desarme__vehiculo_desarme__marca__nombre"), "revenue": Decimal(r.get("revenue") or 0)} for r in qs]


def top_modelos(empresa, limit=10, fecha_desde=None, fecha_hasta=None):
    qs = LineaRepuesto.objects.filter(
        documento__empresa=empresa, documento__estado="EMITIDO", origen_repuesto=ORIGEN_DESARME
    )
    if fecha_desde:
        qs = qs.filter(documento__fecha_emision__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(documento__fecha_emision__lte=fecha_hasta)
    qs = (
        qs.values("pieza_desarme__vehiculo_desarme__modelo__nombre")
        .annotate(revenue=Sum(F("precio_unitario") * F("cantidad")))
        .order_by("-revenue")[:limit]
    )
    return [{"modelo": r.get("pieza_desarme__vehiculo_desarme__modelo__nombre"), "revenue": Decimal(r.get("revenue") or 0)} for r in qs]


def top_roi_vehiculos(empresa, limit=10):
    vehs = VehiculoDesarme.objects.filter(empresa=empresa, es_placeholder=False)
    scored = []
    for v in vehs:
        roi = calcular_roi_vehiculo(v)
        scored.append({"vehiculo_id": v.id, "patente": v.patente, "roi": roi})
    scored.sort(key=lambda x: float(x.get("roi") or 0), reverse=True)
    return scored[:limit]


# --- Fase 1: Reportes de negocio para el dueño de la desarmaduría ---


def vehiculos_zombis(empresa, limit=10):
    """
    Vehículos con peor health_score: capital atrapado sin retorno.
    Le dice al dueño cuáles vehículos le están perjudicando ahora mismo.
    """
    vehs = VehiculoDesarme.objects.filter(empresa=empresa, es_placeholder=False)
    scored = []
    for v in vehs:
        score = health_score(v)
        dead = inventario_muerto(v)
        scored.append(
            {
                "vehiculo_id": v.id,
                "patente": v.patente or v.vin or f"ID {v.id}",
                "marca": v.get_marca_display(),
                "modelo": v.get_modelo_display(),
                "health_score": score,
                "inventario_muerto": dead,
            }
        )
    scored.sort(key=lambda x: x["health_score"] if x["health_score"] is not None else 0)
    return scored[:limit]


def inventario_muerto_total(empresa):
    """
    Valor contable total de piezas en estados no vendibles (DANADA, SCRAP, FALTANTE)
    de toda la flota activa. Un solo número que representa capital perdido.
    """
    qs = PiezaDesarme.objects.filter(
        vehiculo_desarme__empresa=empresa,
        vehiculo_desarme__es_placeholder=False,
        estado_pieza__in=[ESTADO_DANADA, ESTADO_SCRAP, ESTADO_FALTANTE],
    )
    agg = qs.aggregate(
        valor=Sum(F("costo_asignado") * F("cantidad")),
        piezas=Sum("cantidad"),
    )
    return {
        "valor_total": Decimal(agg["valor"] or 0),
        "piezas_count": int(agg["piezas"] or 0),
    }


def top_proveedores(empresa, limit=10):
    """
    Proveedores (VendedorDesarme) rankeados por ROI promedio de los vehículos
    comprados a ellos. Le dice al dueño a quién comprarle más y a quién no.
    """
    proveedores = VendedorDesarme.objects.filter(empresa=empresa)
    result = []
    for prov in proveedores:
        vehs = VehiculoDesarme.objects.filter(
            empresa=empresa, vendedor_desarme=prov, es_placeholder=False
        )
        if not vehs.exists():
            continue
        total_ganancia = Decimal("0")
        total_inversion = Decimal("0")
        count = 0
        for v in vehs:
            total_ganancia += calcular_ganancia_vehiculo(v)
            total_inversion += calcular_inversion_total_vehiculo(v)
            count += 1
        roi = (
            (total_ganancia / total_inversion) * Decimal("100")
            if total_inversion > 0
            else Decimal("0")
        )
        result.append(
            {
                "proveedor_id": prov.id,
                "nombre": prov.nombre,
                "vehiculos_comprados": count,
                "ganancia_total": total_ganancia,
                "roi_promedio": roi,
            }
        )
    result.sort(key=lambda x: float(x["roi_promedio"]), reverse=True)
    return result[:limit]


def aging_inventario(empresa):
    """
    Piezas DISPONIBLES agrupadas por antigüedad desde fecha_extraccion.
    Identifica inventario estancado que ocupa espacio y capital.
    """
    today = timezone.now().date()
    base_qs = PiezaDesarme.objects.filter(
        vehiculo_desarme__empresa=empresa,
        vehiculo_desarme__es_placeholder=False,
        estado_pieza=ESTADO_DISPONIBLE,
        activo=True,
        fecha_extraccion__isnull=False,
    )
    buckets = [
        ("0-30 días", today - timedelta(days=30), today),
        ("30-90 días", today - timedelta(days=90), today - timedelta(days=31)),
        ("90-180 días", today - timedelta(days=180), today - timedelta(days=91)),
        ("180+ días", None, today - timedelta(days=181)),
    ]
    result = []
    for label, fecha_min, fecha_max in buckets:
        qs = base_qs.filter(fecha_extraccion__lte=fecha_max)
        if fecha_min:
            qs = qs.filter(fecha_extraccion__gte=fecha_min)
        agg = qs.aggregate(
            valor=Sum(F("costo_asignado") * F("cantidad")),
            piezas=Sum("cantidad"),
        )
        result.append(
            {
                "bucket": label,
                "valor": Decimal(agg["valor"] or 0),
                "piezas": int(agg["piezas"] or 0),
            }
        )
    return result


def top_vendedores(empresa, limit=10, fecha_desde=None, fecha_hasta=None):
    """
    Top vendedores (TeamMember) por ingresos de piezas de desarme vendidas.
    Solo cuenta ventas donde se registró vendedor — ventas anteriores a esta
    funcionalidad quedan fuera (vendedor=NULL), no se infiere retroactivamente.
    """
    qs = LineaRepuesto.objects.filter(
        documento__empresa=empresa,
        documento__estado="EMITIDO",
        origen_repuesto=ORIGEN_DESARME,
        vendedor__isnull=False,
    )
    if fecha_desde:
        qs = qs.filter(documento__fecha_emision__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(documento__fecha_emision__lte=fecha_hasta)
    qs = (
        qs.values("vendedor_id")
        .annotate(revenue=Sum(F("precio_unitario") * F("cantidad")), sold=Sum("cantidad"))
        .order_by("-revenue")[:limit]
    )

    from taller.models.team_member import TeamMember

    vendedor_ids = [r["vendedor_id"] for r in qs]
    vendedores_map = {}
    for tm in TeamMember.objects.filter(id__in=vendedor_ids).select_related("user"):
        nombre = ""
        if tm.user_id:
            nombre = (tm.user.get_full_name() or "").strip() or tm.user.username
        vendedores_map[tm.id] = nombre or f"Vendedor #{tm.id}"

    result = []
    for r in qs:
        vid = r["vendedor_id"]
        result.append(
            {
                "vendedor_id": vid,
                "nombre": vendedores_map.get(vid, f"Vendedor #{vid}"),
                "revenue": Decimal(r.get("revenue") or 0),
                "sold": int(r.get("sold") or 0),
            }
        )
    return result