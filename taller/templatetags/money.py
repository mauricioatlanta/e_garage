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
    country_code = str(country or "CL").strip().upper()
    if country_code == "CL":
        return money_clp(value)

    n = _to_decimal(value)
    symbol_map = {
        "US": "$",
        "MX": "$",
        "VE": "Bs. ",
        "PE": "S/ ",
        "BR": "R$ ",
    }
    symbol = symbol_map.get(country_code, "$")
    return f"{symbol}{n:,.2f}"
