from decimal import Decimal, ROUND_HALF_UP
from django import template

register = template.Library()

def _fmt_currency(amount: Decimal, code: str, decs: int):
    if amount is None:
        amount = Decimal("0")
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    q = Decimal("1") if decs == 0 else Decimal("0." + "0"*(decs-1) + "1")
    amount = amount.quantize(q, rounding=ROUND_HALF_UP)
    # Separadores: miles con punto y decimales con coma (CL) / punto (US)
    s = f"{amount:,.{decs}f}"
    if code == "CLP":
        # 1.234.567 (sin decimales por defecto)
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        if decs == 0:
            s = s.split(",")[0]
    return s

@register.filter
def money_fmt(value, moneda_dict):
    """
    Uso: {{ obj.total|money_fmt:empresa_moneda }}
    donde empresa_moneda = {"simbolo":"$", "codigo":"CLP|USD", "decimales":0|2}
    """
    code = (moneda_dict or {}).get("codigo", "CLP")
    decs = int((moneda_dict or {}).get("decimales", 0))
    symb = (moneda_dict or {}).get("simbolo", "$")
    num = _fmt_currency(value, code, decs)
    # Prefijo corto: US$ / CLP$ si quieres distinguir
    prefix = f"{symb}"
    if code == "USD":
        prefix = "US$"
    elif code == "CLP":
        prefix = "CLP$" if decs > 0 else "$"
    return f"{prefix}{num}"

def _num_to_words_es(amount: Decimal, code: str):
    try:
        from num2words import num2words  # opcional si lo tienes en requirements
    except Exception:
        # Fallback simple
        return f"{code} {amount}"
    entero = int(amount)
    cent = int((amount - Decimal(entero)) * 100)
    moneda = "pesos chilenos" if code == "CLP" else "dólares"
    if cent > 0:
        return f"{num2words(entero, lang='es')} {moneda} con {num2words(cent, lang='es')} centavos"
    return f"{num2words(entero, lang='es')} {moneda}"

def _num_to_words_en(amount: Decimal, code: str):
    try:
        from num2words import num2words
    except Exception:
        return f"{code} {amount}"
    entero = int(amount)
    cent = int((amount - Decimal(entero)) * 100)
    currency = "dollars" if code == "USD" else "pesos"
    if cent > 0:
        return f"{num2words(entero, lang='en')} {currency} and {num2words(cent, lang='en')} cents"
    return f"{num2words(entero, lang='en')} {currency}"

@register.filter
def money_words(value, moneda_dict):
    """
    Uso: {{ obj.total|money_words:empresa_moneda }}
    Requiere num2words (opcional). Si no está, muestra "CLP 123456"/"USD 123.45".
    """
    code = (moneda_dict or {}).get("codigo", "CLP")
    decs = int((moneda_dict or {}).get("decimales", 0))
    if value is None:
        value = Decimal("0")
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    q = Decimal("1") if decs == 0 else Decimal("0." + "0"*(decs-1) + "1")
    amount = value.quantize(q, rounding=ROUND_HALF_UP)

    if code == "USD":
        return _num_to_words_en(amount, code)
    # Default ES/CL
    return _num_to_words_es(amount, code)
