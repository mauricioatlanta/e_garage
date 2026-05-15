"""
Utilidades para conversión entre millas y kilómetros.

Estrategia: Guardar SIEMPRE en kilómetros (km) en la base de datos para consistencia
en reportes y KPIs. Convertir solo en la capa de presentación y formularios.
"""

MILES_TO_KM = 1.609344


def miles_to_km(mi: int | float | None) -> int | None:
    """
    Convierte millas a kilómetros.

    Args:
        mi: Valor en millas (puede ser int, float o None)

    Returns:
        int: Valor en kilómetros redondeado, o None si el input es None/0
    """
    if mi is None or mi == 0:
        return None
    return int(round((mi or 0) * MILES_TO_KM))


def km_to_miles(km: int | float | None) -> int | None:
    """
    Convierte kilómetros a millas.

    Args:
        km: Valor en kilómetros (puede ser int, float o None)

    Returns:
        int: Valor en millas redondeado, o None si el input es None/0
    """
    if km is None or km == 0:
        return None
    return int(round((km or 0) / MILES_TO_KM))
