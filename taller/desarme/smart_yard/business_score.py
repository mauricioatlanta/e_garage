"""
Smart Yard - Business Score

Interpreta el historial financiero real de un VehiculoDesarme.

Fuente de verdad:
- VehiculoFinancialSnapshot

NO recalcula:
- ROI
- recuperación
- ingresos
- costos

Solo transforma indicadores financieros existentes
en una puntuación para usar como referencia confiable.
"""

from decimal import Decimal


BUSINESS_WEIGHTS = {
    "roi": Decimal("0.40"),
    "recuperacion": Decimal("0.25"),
    "health": Decimal("0.20"),
    "evidencia": Decimal("0.15"),
}


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def calculate_evidence_score(snapshot, vehiculo):
    """
    Evalúa calidad de evidencia histórica.

    No mide éxito.
    Mide qué tan respaldado está el dato.
    """

    eventos = getattr(snapshot, "source_event_count", 0) or 0

    try:
        piezas = vehiculo.piezas_desarme.count()
    except Exception:
        piezas = 0

    score_eventos = min(100, eventos * 5)
    score_piezas = min(100, piezas * 2)

    return round(
        (score_eventos * 0.5) +
        (score_piezas * 0.5),
        2,
    )


def calculate_business_success_score(vehiculo):
    """
    Retorna desempeño comercial histórico.

    Estados:
    - NO_HISTORY: sin snapshot financiero
    - ACTIVE_HISTORY: datos insuficientes
    - REFERENCE: referencia confiable
    """

    snapshot = (
        vehiculo.financial_snapshots
        .order_by("-fecha")
        .first()
    )

    if not snapshot:
        return {
            "score": 0,
            "status": "NO_HISTORY",
            "snapshot": False,
            "roi": 0,
            "recuperacion": 0,
            "health": 0,
            "evidencia": 0,
        }

    roi = Decimal(snapshot.roi_pct or 0)
    recuperacion = Decimal(snapshot.recuperacion_pct or 0)
    health = Decimal(snapshot.health_score or 0)

    evidencia = Decimal(
        calculate_evidence_score(snapshot, vehiculo)
    )

    # Normalización:
    # ROI y recuperación pueden superar 100%
    roi_score = min(roi, Decimal("100"))
    recuperacion_score = min(recuperacion, Decimal("100"))

    score = (
        roi_score * BUSINESS_WEIGHTS["roi"]
        +
        recuperacion_score * BUSINESS_WEIGHTS["recuperacion"]
        +
        health * BUSINESS_WEIGHTS["health"]
        +
        evidencia * BUSINESS_WEIGHTS["evidencia"]
    )

    score = round(clamp(float(score)), 2)

    if evidencia < 30:
        status = "LOW_DATA"

    elif score >= 75:
        status = "REFERENCE"

    else:
        status = "WEAK_REFERENCE"

    return {
        "score": score,
        "status": status,
        "snapshot": True,
        "roi": float(roi),
        "recuperacion": float(recuperacion),
        "health": float(health),
        "evidencia": float(evidencia),
        "source_events": snapshot.source_event_count,
    }
