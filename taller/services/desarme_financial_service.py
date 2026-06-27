from decimal import Decimal

from django.db.models import F, Sum, Min, Max

from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE, ESTADO_RESERVADA
from taller.models.vehiculo_desarme import VehiculoDesarme


def _lineas_desarme_para_vehiculo(vehiculo):
    return LineaRepuesto.objects.filter(
        origen_repuesto=ORIGEN_DESARME, pieza_desarme__vehiculo_desarme_id=vehiculo.id, documento__estado="EMITIDO"
    )


def calcular_ingresos_vehiculo(vehiculo):
    """Ingresos realizados por ventas de piezas asociadas al vehículo."""
    agg = _lineas_desarme_para_vehiculo(vehiculo).aggregate(v=Sum(F("precio_unitario") * F("cantidad")))
    return Decimal(agg.get("v") or 0)


def _vendidos_por_pieza_vehiculo(vehiculo):
    qs = (
        _lineas_desarme_para_vehiculo(vehiculo)
        .values("pieza_desarme")
        .annotate(sold=Sum("cantidad"))
    )
    return {item["pieza_desarme"]: int(item["sold"] or 0) for item in qs}


def calcular_inversion_total_vehiculo(vehiculo):
    """Inversión histórica asociada al vehículo (suma costos imputados por unidad)."""
    piezas = PiezaDesarme.objects.filter(vehiculo_desarme_id=vehiculo.id)
    sold_map = _vendidos_por_pieza_vehiculo(vehiculo)
    total = Decimal("0")
    for p in piezas.only("id", "costo_asignado", "cantidad"):
        unidad_cost = Decimal(p.costo_asignado or 0)
        qty_ever = int(p.cantidad or 0) + int(sold_map.get(p.id, 0))
        total += unidad_cost * qty_ever
    return total


def calcular_costo_vendido_vehiculo(vehiculo):
    """Costo de las unidades ya vendidas del vehículo."""
    lines = _lineas_desarme_para_vehiculo(vehiculo).select_related("pieza_desarme")
    total = Decimal("0")
    for ln in lines:
        cantidad = int(ln.cantidad or 0)
        if cantidad <= 0:
            continue
        costo_unit = None
        if getattr(ln, "costo_linea", None) not in (None, ""):
            try:
                costo_unit = Decimal(str(ln.costo_linea))
            except Exception:
                costo_unit = None
        if costo_unit is None:
            pieza = getattr(ln, "pieza_desarme", None)
            costo_unit = Decimal(pieza.costo_asignado or 0) if pieza is not None else Decimal("0")
        total += costo_unit * cantidad
    return total


def calcular_ganancia_vehiculo(vehiculo):
    ingresos = calcular_ingresos_vehiculo(vehiculo)
    costo_vendido = calcular_costo_vendido_vehiculo(vehiculo)
    return ingresos - costo_vendido


def calcular_recuperacion_vehiculo(vehiculo):
    inversion = calcular_inversion_total_vehiculo(vehiculo)
    if inversion == 0:
        return Decimal("0")
    ingresos = calcular_ingresos_vehiculo(vehiculo)
    return (ingresos / inversion) * Decimal("100")


def calcular_roi_vehiculo(vehiculo):
    inversion = calcular_inversion_total_vehiculo(vehiculo)
    if inversion == 0:
        return Decimal("0")
    ganancia = calcular_ganancia_vehiculo(vehiculo)
    return (ganancia / inversion) * Decimal("100")


def calcular_inventario_vivo_vehiculo(vehiculo):
    """Devuelve dict {valor_contable, valor_mercado} para el inventario vivo del vehículo."""
    piezas = PiezaDesarme.objects.filter(vehiculo_desarme_id=vehiculo.id)
    valor_contable = Decimal("0")
    valor_mercado = Decimal("0")
    for p in piezas.only("cantidad", "costo_asignado", "precio_sugerido", "precio_referencia", "precio_venta_sugerido"):
        qty = int(p.cantidad or 0)
        if qty <= 0:
            continue
        costo = Decimal(p.costo_asignado or 0)
        # precio de mercado preferido: precio_sugerido > precio_referencia > precio_venta_sugerido
        mercado_unit = None
        for cand in (getattr(p, "precio_sugerido", None), getattr(p, "precio_referencia", None), getattr(p, "precio_venta_sugerido", None)):
            if cand not in (None, ""):
                try:
                    mercado_unit = Decimal(cand)
                    break
                except Exception:
                    mercado_unit = None
        mercado_unit = mercado_unit or Decimal("0")
        valor_contable += costo * qty
        valor_mercado += mercado_unit * qty
    return {"valor_contable": valor_contable, "valor_mercado": valor_mercado}


def calcular_dias_recuperacion(vehiculo):
    """Dias entre ingreso y primera venta; si no hay ventas devuelve None."""
    if not getattr(vehiculo, "fecha_ingreso_desarme", None):
        return None
    qs = _lineas_desarme_para_vehiculo(vehiculo).values_list("documento__fecha_emision", flat=True)
    first = qs.order_by("documento__fecha_emision").first()
    if not first:
        return None
    first_date = first.date() if hasattr(first, "date") else first

    ingreso = vehiculo.fecha_ingreso_desarme
    ingreso_date = ingreso.date() if hasattr(ingreso, "date") else ingreso

    delta = first_date - ingreso_date

    return delta.days if hasattr(delta, "days") else None


def calcular_estado_financiero(vehiculo):
    """Determina estado financiero del vehículo: AGOTADO, RECUPERADO, CERRADO, ACTIVO."""
    # AGOTADO: no quedan piezas vendibles reales
    vendibles_exist = PiezaDesarme.objects.filter(
        vehiculo_desarme_id=vehiculo.id,
        activo=True,
        cantidad__gt=0,
        estado_pieza__in=[ESTADO_DISPONIBLE, ESTADO_RESERVADA],
    ).exists()
    inventario = calcular_inventario_vivo_vehiculo(vehiculo)
    inventario_contable = inventario.get("valor_contable")
    recuperacion_pct = calcular_recuperacion_vehiculo(vehiculo)

    estado = "ACTIVO"
    if not vendibles_exist:
        estado = "AGOTADO"
        # CERRADO: no quedan piezas y no hay inventario contable
        if inventario_contable == 0:
            estado = "CERRADO"
    # RECUPERADO: recuperación >= 100%
    if recuperacion_pct >= Decimal("100"):
        estado = "RECUPERADO"

    return estado


# Agregaciones por empresa: iteran sobre vehículos de la empresa
def calcular_inversion_total(empresa):
    total = Decimal("0")
    vehs = VehiculoDesarme.objects.filter(empresa=empresa)
    for v in vehs:
        total += calcular_inversion_total_vehiculo(v)
    return total


def calcular_ingresos_realizados(empresa):
    total = Decimal("0")
    vehs = VehiculoDesarme.objects.filter(empresa=empresa)
    for v in vehs:
        total += calcular_ingresos_vehiculo(v)
    return total


def calcular_roi(empresa):
    inversion = calcular_inversion_total(empresa)
    if inversion == 0:
        return Decimal("0")
    ganancia = Decimal("0")
    vehs = VehiculoDesarme.objects.filter(empresa=empresa)
    for v in vehs:
        ganancia += calcular_ganancia_vehiculo(v)
    return (ganancia / inversion) * Decimal("100")

