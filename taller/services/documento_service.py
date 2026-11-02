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
    # Reutilizar la misma lógica/tasa/quantize del modelo Documento
    # para evitar divergencia con Documento.recompute_totals().

    rep = documento._sum_repuesto()
    srv = documento._sum_servicio()
    osrv = documento._sum_otro_servicio()

    rep = documento._q(rep)
    srv = documento._q(srv)
    osrv = documento._q(osrv)

    desc = getattr(documento, "descuento", Decimal("0")) or Decimal("0")
    desc = documento._q(desc)

    rate = documento._resolve_tax_rate()  # porcentaje, ej: 19.0

    if getattr(documento, "apply_vat", True):
        tax_base = rep
    else:
        tax_base = Decimal("0")

    iva = tax_base * rate / Decimal("100.0")
    iva = documento._q(iva)

    subtotal = rep + srv + osrv
    total = subtotal - desc + iva
    total = documento._q(total)

    return {
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "total_repuestos": rep,
        "total_servicios": srv,
        "total_otros": osrv,
        "descuento": desc,
        "iva_rate": rate,
    }
