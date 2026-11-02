from decimal import ROUND_HALF_UP, Decimal

CLP_PLACES = Decimal("1")  # 0 decimales
USD_PLACES = Decimal("0.01")  # 2 decimales


def money_quantize(amount: Decimal, pais: str) -> Decimal:
    """
    Quantiza un monto según las reglas de decimales del país.

    Usa configuración centralizada para determinar decimales.

    Args:
        amount: Monto a quantizar
        pais: Código de país (ISO 3166-1 alpha-2)

    Returns:
        Decimal: Monto quantizado según reglas del país
    """
    from taller.utils.country_config import get_currency_decimals

    if amount is None:
        amount = Decimal("0")

    decimals = get_currency_decimals(pais)
    places = CLP_PLACES if decimals == 0 else USD_PLACES
    return amount.quantize(places, rounding=ROUND_HALF_UP)
