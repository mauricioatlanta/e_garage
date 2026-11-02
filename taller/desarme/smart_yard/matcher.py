"""
Smart Yard - Technical Matcher

Calcula similitud técnica entre vehículos de desarme.

No modifica datos.
Solo analiza referencias.
"""

from decimal import Decimal


PESOS_SMART_YARD = {
    "modelo": Decimal("25"),
    "motor": Decimal("25"),
    "marca": Decimal("15"),
    "caja": Decimal("15"),
    "anio": Decimal("10"),
    "carroceria": Decimal("10"),
}


def calculate_technical_score(nuevo, historico):
    scores = {
        "modelo": compare_fk(nuevo, historico, "modelo_id"),
        "motor": compare_fk(nuevo, historico, "motor_id"),
        "marca": compare_fk(nuevo, historico, "marca_id"),
        "caja": compare_fk(nuevo, historico, "caja_id"),
        "anio": compare_anio(nuevo, historico),
        "carroceria": compare_field(
            nuevo,
            historico,
            "tipo_carroceria",
        ),
    }

    total = Decimal("0")

    for key, weight in PESOS_SMART_YARD.items():
        total += Decimal(str(scores[key])) * weight / Decimal("100")

    return round(total, 2)


def compare_fk(a, b, field):
    value_a = getattr(a, field, None)
    value_b = getattr(b, field, None)

    if value_a is None or value_b is None:
        return 0

    return 100 if value_a == value_b else 0


def compare_field(a, b, field):
    return (
        100
        if getattr(a, field, None) == getattr(b, field, None)
        else 0
    )


def compare_anio(a, b):
    anio_a = getattr(a, "anio", None)
    anio_b = getattr(b, "anio", None)

    if not anio_a or not anio_b:
        return 0

    diferencia = abs(anio_a - anio_b)

    if diferencia == 0:
        return 100

    if diferencia <= 2:
        return 75

    if diferencia <= 5:
        return 50

    return 25
