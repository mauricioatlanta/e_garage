# taller/templatetags/money.py
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _to_decimal(v):
    try:
        return Decimal(v)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(0)


@register.filter
def money_clp(value):
    n = _to_decimal(value)
    # $12.345 (sin decimales)
    s = f"{n:,.0f}"  # 12,345
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")  # 12.345
    return f"${s}"


@register.filter
def money_by_country(value, country="CL"):
    """
    Formatea moneda según país usando configuración centralizada.

    Args:
        value: Monto a formatear
        country: Código de país (ISO 3166-1 alpha-2)

    Returns:
        str: Monto formateado según reglas del país
    """
    from taller.utils.country_config import format_currency

    country_code = str(country or "CL").strip().upper()

    # Caso especial para CL (sin decimales)
    if country_code == "CL":
        return money_clp(value)

    # Usar configuración centralizada para otros países
    return format_currency(value, country_code, include_symbol=True)
