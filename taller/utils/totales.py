from decimal import ROUND_HALF_UP, Decimal

IVA_CHILE = Decimal("0.19")


def redondear(valor):
    return Decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def totales_chile(lineas_repuesto, lineas_servicio):
    subtotal_rep = (
        sum((lr.cantidad * lr.precio_unitario - lr.descuento) for lr in lineas_repuesto)
        or 0
    )
    subtotal_ser = (
        sum((ls.cantidad * ls.precio_unitario - ls.descuento) for ls in lineas_servicio)
        or 0
    )

    subtotal_rep = Decimal(subtotal_rep)
    subtotal_ser = Decimal(subtotal_ser)

    iva = redondear(subtotal_rep * IVA_CHILE)  # IVA SOLO sobre repuestos
    total = subtotal_rep + subtotal_ser + iva

    return {
        "subtotal_repuestos": redondear(subtotal_rep),
        "subtotal_servicios": redondear(subtotal_ser),
        "iva": iva,
        "total": redondear(total),
    }
