# -*- coding: utf-8 -*-
"""
Servicios de negocio para Documentos

Convenciones:
- Cálculo de totales con impuestos por país
- Chile: IVA 19% solo a repuestos
- USA: sales tax por ubicación
- KPIs usan solo fecha_emision (NO fecha_creacion)
- Cálculo financiero con Decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
- Usar campo subtotal de línea si existe, NO calcular a mano
"""
from decimal import Decimal, ROUND_HALF_UP

from taller.impuestos.engine import resolve_tax_rate


def _quantize_money(value):
    """
    Redondear valor financiero a 2 decimales con ROUND_HALF_UP (estándar financiero).

    Args:
        value (Decimal): Valor a redondear

    Returns:
        Decimal: Valor redondeado a 2 decimales

    Ejemplos:
        >>> _quantize_money(Decimal('123.456'))
        Decimal('123.46')
        >>> _quantize_money(Decimal('123.454'))
        Decimal('123.45')
        >>> _quantize_money(Decimal('123.455'))
        Decimal('123.46')  # ROUND_HALF_UP

    Importante:
        Este es el estándar financiero. SIEMPRE usar esto en cálculos de dinero.
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_totales(documento):
    """
    Calcula los totales de un documento con impuestos según país.

    Args:
        documento: Instancia de Documento

    Returns:
        Documento con campos de totales actualizados:
            - subtotal_repuestos
            - subtotal_servicios
            - iva_repuestos
            - iva_servicios
            - total

    Lógica:
        1. Suma subtotales de repuestos (con descuentos)
        2. Suma subtotales de servicios (con descuentos)
        3. Resuelve tax rate para repuestos
        4. Resuelve tax rate para servicios
        5. Calcula impuestos
        6. Calcula total final

    Convenciones:
        - Chile: IVA 19% solo repuestos (servicios 0%)
        - USA: sales tax por ubicación
        - Brasil: ICMS 18% repuestos
        - Perú: IGV 18% ambos
        - Venezuela: IVA 16% ambos

    Ejemplo:
        >>> documento = Documento.objects.get(pk=1)
        >>> calcular_totales(documento)
        >>> documento.save()
        >>> print(documento.total)  # Total calculado con impuestos
    """

    # === 1. CALCULAR SUBTOTALES ===

    total_parts = Decimal("0.00")
    total_services = Decimal("0.00")

    # Sumar líneas de repuestos
    for lr in documento.lineas_repuesto.all():
        # ✅ IMPORTANTE: Usar campo subtotal si existe (NO calcular a mano)
        if hasattr(lr, "subtotal") and lr.subtotal is not None:
            # Usar subtotal precalculado de la línea
            subtotal_linea = lr.subtotal
        else:
            # Calcular: cantidad * precio_unitario - descuento
            subtotal_linea = Decimal(str(lr.cantidad or 0)) * Decimal(str(lr.precio_unitario or 0))

            # Aplicar descuento si existe
            if hasattr(lr, "descuento") and lr.descuento:
                descuento_valor = subtotal_linea * (Decimal(str(lr.descuento)) / Decimal("100"))
                subtotal_linea -= descuento_valor

            # ✅ Redondear subtotal de línea
            subtotal_linea = _quantize_money(subtotal_linea)

        total_parts += subtotal_linea

    # Sumar líneas de servicios
    for ls in documento.lineas_servicio.all():
        # ✅ IMPORTANTE: Usar campo subtotal si existe (NO calcular a mano)
        if hasattr(ls, "subtotal") and ls.subtotal is not None:
            # Usar subtotal precalculado de la línea
            subtotal_linea = ls.subtotal
        else:
            # Calcular: cantidad * precio_unitario - descuento
            subtotal_linea = Decimal(str(ls.cantidad or 0)) * Decimal(str(ls.precio_unitario or 0))

            # Aplicar descuento si existe
            if hasattr(ls, "descuento") and ls.descuento:
                descuento_valor = subtotal_linea * (Decimal(str(ls.descuento)) / Decimal("100"))
                subtotal_linea -= descuento_valor

            # ✅ Redondear subtotal de línea
            subtotal_linea = _quantize_money(subtotal_linea)

        total_services += subtotal_linea

    # ✅ Redondear totales de categorías
    total_parts = _quantize_money(total_parts)
    total_services = _quantize_money(total_services)

    # === 2. DETERMINAR CIUDAD DE DESTINO (para sales tax) ===

    ship_to_city = None

    # Prioridad 1: Ciudad del cliente (billing_address)
    if hasattr(documento, "cliente") and documento.cliente:
        if hasattr(documento.cliente, "billing_address") and documento.cliente.billing_address:
            ship_to_city = documento.cliente.billing_address.city

    # Prioridad 2: Ciudad de la empresa (legal_address)
    if not ship_to_city and hasattr(documento, "empresa") and documento.empresa:
        if hasattr(documento.empresa, "config") and documento.empresa.config:
            if (
                hasattr(documento.empresa.config, "legal_address")
                and documento.empresa.config.legal_address
            ):
                ship_to_city = documento.empresa.config.legal_address.city

    # Prioridad 3: Usar ciudad_usa legacy (si existe)
    if not ship_to_city and hasattr(documento, "cliente") and documento.cliente:
        if hasattr(documento.cliente, "ciudad_usa") and documento.cliente.ciudad_usa:
            ship_to_city = documento.cliente.ciudad_usa

    # === 3. RESOLVER TASAS DE IMPUESTO ===

    rate_parts, inc_parts = resolve_tax_rate(documento.empresa, ship_to_city, "parts")

    rate_services, inc_services = resolve_tax_rate(documento.empresa, ship_to_city, "services")

    # === 4. CALCULAR IMPUESTOS ===

    # Impuesto sobre repuestos
    # ✅ Usar _quantize_money para estándar financiero ROUND_HALF_UP
    tax_parts = _quantize_money(total_parts * Decimal(str(rate_parts)))

    # Impuesto sobre servicios (Chile típico: rate_services = 0)
    tax_services = _quantize_money(total_services * Decimal(str(rate_services)))

    # === 5. ACTUALIZAR CAMPOS DEL DOCUMENTO ===

    documento.subtotal_repuestos = total_parts
    documento.subtotal_servicios = total_services
    documento.iva_repuestos = tax_parts
    documento.iva_servicios = tax_services

    # ✅ Total final redondeado
    documento.total = _quantize_money(total_parts + total_services + tax_parts + tax_services)

    # Campos opcionales (si existen en el modelo)
    if hasattr(documento, "subtotal"):
        documento.subtotal = total_parts + total_services

    if hasattr(documento, "impuesto_total"):
        documento.impuesto_total = tax_parts + tax_services

    if hasattr(documento, "tasa_impuesto_repuestos"):
        documento.tasa_impuesto_repuestos = rate_parts

    if hasattr(documento, "tasa_impuesto_servicios"):
        documento.tasa_impuesto_servicios = rate_services

    return documento


def recalcular_y_guardar(documento):
    """
    Recalcula totales y guarda el documento.

    Args:
        documento: Instancia de Documento

    Returns:
        Documento guardado con totales actualizados

    Ejemplo:
        >>> from taller.documentos.services import recalcular_y_guardar
        >>> recalcular_y_guardar(documento)
    """
    calcular_totales(documento)
    documento.save(
        update_fields=[
            "subtotal_repuestos",
            "subtotal_servicios",
            "iva_repuestos",
            "iva_servicios",
            "total",
        ]
    )
    return documento


def preview_totales(documento) -> dict:
    """
    Calcula totales sin guardar (preview).

    Args:
        documento: Instancia de Documento

    Returns:
        dict con totales calculados:
            - subtotal_parts: Subtotal de repuestos
            - subtotal_services: Subtotal de servicios
            - tax_parts: Impuesto sobre repuestos
            - tax_services: Impuesto sobre servicios
            - subtotal: Subtotal general
            - tax_total: Impuesto total
            - total: Total final
            - tax_info_parts: Info del impuesto de repuestos
            - tax_info_services: Info del impuesto de servicios

    Útil para:
        - Mostrar preview antes de guardar
        - APIs que retornan cálculos
        - Testing

    Ejemplo:
        >>> totales = preview_totales(documento)
        >>> print(totales['total'])  # Total calculado
        >>> print(totales['tax_info_parts'])  # Info del impuesto
    """
    from taller.impuestos.engine import get_tax_info

    # Calcular sin modificar documento
    total_parts = Decimal("0.00")
    total_services = Decimal("0.00")

    for lr in documento.lineas_repuesto.all():
        # ✅ Usar subtotal si existe
        if hasattr(lr, "subtotal") and lr.subtotal is not None:
            subtotal_linea = lr.subtotal
        else:
            subtotal_linea = Decimal(str(lr.cantidad or 0)) * Decimal(str(lr.precio_unitario or 0))
            if hasattr(lr, "descuento") and lr.descuento:
                descuento_valor = subtotal_linea * (Decimal(str(lr.descuento)) / Decimal("100"))
                subtotal_linea -= descuento_valor
            subtotal_linea = _quantize_money(subtotal_linea)
        total_parts += subtotal_linea

    for ls in documento.lineas_servicio.all():
        # ✅ Usar subtotal si existe
        if hasattr(ls, "subtotal") and ls.subtotal is not None:
            subtotal_linea = ls.subtotal
        else:
            subtotal_linea = Decimal(str(ls.cantidad or 0)) * Decimal(str(ls.precio_unitario or 0))
            if hasattr(ls, "descuento") and ls.descuento:
                descuento_valor = subtotal_linea * (Decimal(str(ls.descuento)) / Decimal("100"))
                subtotal_linea -= descuento_valor
            subtotal_linea = _quantize_money(subtotal_linea)
        total_services += subtotal_linea

    # ✅ Redondear totales
    total_parts = _quantize_money(total_parts)
    total_services = _quantize_money(total_services)

    # Determinar ciudad
    ship_to_city = None
    if hasattr(documento, "cliente") and documento.cliente:
        if hasattr(documento.cliente, "billing_address") and documento.cliente.billing_address:
            ship_to_city = documento.cliente.billing_address.city

    # Resolver tasas
    rate_parts, inc_parts = resolve_tax_rate(documento.empresa, ship_to_city, "parts")
    rate_services, inc_services = resolve_tax_rate(documento.empresa, ship_to_city, "services")

    # Calcular impuestos con _quantize_money
    tax_parts = _quantize_money(total_parts * Decimal(str(rate_parts)))
    tax_services = _quantize_money(total_services * Decimal(str(rate_services)))

    # Obtener info detallada
    tax_info_parts = get_tax_info(documento.empresa, ship_to_city, "parts")
    tax_info_services = get_tax_info(documento.empresa, ship_to_city, "services")

    # ✅ Todos los totales redondeados
    subtotal = _quantize_money(total_parts + total_services)
    tax_total = _quantize_money(tax_parts + tax_services)
    total = _quantize_money(total_parts + total_services + tax_parts + tax_services)

    return {
        "subtotal_parts": total_parts,
        "subtotal_services": total_services,
        "tax_parts": tax_parts,
        "tax_services": tax_services,
        "subtotal": subtotal,
        "tax_total": tax_total,
        "total": total,
        "tax_info_parts": tax_info_parts,
        "tax_info_services": tax_info_services,
    }


def calcular_totales_con_descuento_global(
    documento, descuento_porcentaje: Decimal = Decimal("0.00")
):
    """
    Calcula totales con un descuento global aplicado al final.

    Args:
        documento: Instancia de Documento
        descuento_porcentaje: Descuento global en porcentaje (ej: 10.00 para 10%)

    Returns:
        Documento con totales actualizados incluyendo descuento global

    Lógica:
        1. Calcular subtotales de líneas
        2. Aplicar descuento global
        3. Calcular impuestos sobre subtotal con descuento
        4. Calcular total final

    Ejemplo:
        >>> calcular_totales_con_descuento_global(documento, Decimal('10.00'))
        >>> # Aplica 10% de descuento global
    """
    # Calcular totales base
    calcular_totales(documento)

    if descuento_porcentaje > 0:
        # Aplicar descuento global al subtotal
        subtotal_antes_descuento = documento.subtotal_repuestos + documento.subtotal_servicios
        descuento_valor = _quantize_money(
            subtotal_antes_descuento * (Decimal(str(descuento_porcentaje)) / Decimal("100"))
        )
        subtotal_con_descuento = _quantize_money(subtotal_antes_descuento - descuento_valor)

        # Recalcular impuestos sobre el subtotal con descuento
        # Proporcional según tipo
        if subtotal_antes_descuento > 0:
            proporcion_parts = documento.subtotal_repuestos / subtotal_antes_descuento
            proporcion_services = documento.subtotal_servicios / subtotal_antes_descuento
        else:
            proporcion_parts = Decimal("0.00")
            proporcion_services = Decimal("0.00")

        subtotal_parts_con_desc = _quantize_money(subtotal_con_descuento * proporcion_parts)
        subtotal_services_con_desc = _quantize_money(subtotal_con_descuento * proporcion_services)

        # Determinar ciudad para tax
        ship_to_city = None
        if hasattr(documento, "cliente") and documento.cliente:
            if hasattr(documento.cliente, "billing_address") and documento.cliente.billing_address:
                ship_to_city = documento.cliente.billing_address.city

        # Resolver tasas
        rate_parts, _ = resolve_tax_rate(documento.empresa, ship_to_city, "parts")
        rate_services, _ = resolve_tax_rate(documento.empresa, ship_to_city, "services")

        # Recalcular impuestos con _quantize_money
        tax_parts = _quantize_money(subtotal_parts_con_desc * Decimal(str(rate_parts)))
        tax_services = _quantize_money(subtotal_services_con_desc * Decimal(str(rate_services)))

        # Actualizar documento
        documento.subtotal_repuestos = subtotal_parts_con_desc
        documento.subtotal_servicios = subtotal_services_con_desc
        documento.iva_repuestos = tax_parts
        documento.iva_servicios = tax_services
        documento.total = _quantize_money(subtotal_con_descuento + tax_parts + tax_services)

        # Guardar descuento si el modelo lo soporta
        if hasattr(documento, "descuento_global"):
            documento.descuento_global = descuento_porcentaje
        if hasattr(documento, "descuento_valor"):
            documento.descuento_valor = descuento_valor

    return documento
