from decimal import Decimal


def _as_decimal(value):
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def calcular_totales(documento):
    total_repuestos = Decimal("0")
    total_servicios = Decimal("0")
    total_otros = Decimal("0")

    for lr in getattr(documento, "lineas_repuesto", []).all():
        cantidad = _as_decimal(getattr(lr, "cantidad", 0))
        precio = _as_decimal(getattr(lr, "precio_unitario", 0))
        descuento_pct = _as_decimal(getattr(lr, "descuento", 0))
        total_repuestos += cantidad * precio * (Decimal("1") - (descuento_pct / Decimal("100")))

    for ls in getattr(documento, "lineas_servicio", []).all():
        cantidad = _as_decimal(getattr(ls, "cantidad", 0))
        precio = _as_decimal(getattr(ls, "precio_unitario", 0))
        descuento_pct = _as_decimal(getattr(ls, "descuento", 0))
        total_servicios += cantidad * precio * (Decimal("1") - (descuento_pct / Decimal("100")))

    for los in getattr(documento, "lineas_otro_servicio", []).all():
        cantidad = _as_decimal(getattr(los, "cantidad", 0))
        precio_cliente = _as_decimal(getattr(los, "precio_cliente", 0))
        total_otros += cantidad * precio_cliente

    iva_rate = Decimal("0.19")
    iva = total_repuestos * iva_rate

    subtotal = total_repuestos + total_servicios + total_otros
    total = subtotal + iva

    return {
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "total_repuestos": total_repuestos,
        "total_servicios": total_servicios,
        "total_otros": total_otros,
        "iva_rate": iva_rate,
    }
