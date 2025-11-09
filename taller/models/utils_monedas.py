from decimal import ROUND_HALF_UP, Decimal

CLP_PLACES = Decimal("1")  # 0 decimales
USD_PLACES = Decimal("0.01")  # 2 decimales


def money_quantize(amount: Decimal, pais: str) -> Decimal:
    if amount is None:
        amount = Decimal("0")
    places = CLP_PLACES if pais == "CL" else USD_PLACES
    return amount.quantize(places, rounding=ROUND_HALF_UP)
