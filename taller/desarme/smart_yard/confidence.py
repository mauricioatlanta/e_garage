"""
Smart Yard - Confidence Engine

Evalúa qué tan confiable es una referencia histórica.

No mide rentabilidad.
Mide calidad de evidencia.
"""


def calculate_data_confidence(
    piezas_totales,
    eventos_financieros,
    dias_historial,
):
    """
    Retorna confianza 0-100.

    Más datos históricos = mayor confianza.
    """

    score_piezas = min(100, piezas_totales * 2)

    score_eventos = min(100, eventos_financieros * 5)

    score_tiempo = min(100, dias_historial / 3)

    return round(
        (
            score_piezas * 0.5
            + score_eventos * 0.3
            + score_tiempo * 0.2
        ),
        2,
    )


def get_reference_status(business_score):
    """
    Clasifica la calidad comercial de una referencia.
    """

    if business_score < 50:
        return "TOXIC"

    if business_score < 70:
        return "WARN"

    return "RECOMMENDED"


def calculate_reference_confidence(
    technical_score,
    business_score,
    data_confidence,
):
    """
    Score final de confianza.

    La evidencia limita la recomendación.
    """

    if business_score < 50:
        return {
            "score": 0,
            "status": "TOXIC",
        }

    score = (
        technical_score * 0.5
        + business_score * 0.3
        + data_confidence * 0.2
    )

    if data_confidence < 30:
        status = "INSUFFICIENT_DATA"
    else:
        status = get_reference_status(business_score)

    return {
        "score": round(score, 2),
        "status": status,
    }
