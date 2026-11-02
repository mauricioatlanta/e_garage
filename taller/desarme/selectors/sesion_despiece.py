"""
Selector de lectura pura para la sesión de despiece de un vehículo.

Contrato: get_sesion_despiece(vehiculo_id, empresa) -> dict
  - Sin efectos secundarios.
  - Agrupa sugerencias por zona con mapeo de estado_visual.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.pieza_desarme import CONDICION_BUENA, CONDICION_EXCELENTE, CONDICION_NUEVA

# Condiciones "buenas" → visual verde; el resto (REGULAR) → amarillo
_CONDICION_VERDE = {CONDICION_BUENA, CONDICION_EXCELENTE, CONDICION_NUEVA}


def _estado_visual(sug: SugerenciaPiezaDesarme) -> str:
    """
    Maps sugerencia estado+condicion → UI color token.
    gris   = PENDIENTE
    verde  = CONFIRMADA con condición buena/excelente/nueva
    amarillo = CONFIRMADA con condición regular o condicion_sugerida vacía
    rojo   = DESCARTADA
    """
    if sug.estado == SugerenciaPiezaDesarme.DESCARTADA:
        return "rojo"
    if sug.estado == SugerenciaPiezaDesarme.CONFIRMADA:
        condicion = sug.condicion_sugerida or CONDICION_BUENA
        return "verde" if condicion in _CONDICION_VERDE else "amarillo"
    return "gris"


def get_sesion_despiece(vehiculo_id: int, empresa) -> dict[str, Any]:
    """
    Returns the full session state for the despiece UI.
    Grouped by zona, with estado_visual per sugerencia.
    """
    vehiculo = VehiculoDesarme.objects.filter(pk=vehiculo_id, empresa=empresa).first()
    if vehiculo is None:
        return {"vehiculo": None, "zonas": [], "resumen": _empty_resumen()}

    sugerencias = list(
        SugerenciaPiezaDesarme.objects
        .filter(empresa=empresa, vehiculo_desarme=vehiculo)
        .order_by("zona", "codigo")
    )

    zonas_dict: dict[str, list] = {}
    for sug in sugerencias:
        zona_key = sug.zona or "Otros"
        zonas_dict.setdefault(zona_key, [])
        zonas_dict[zona_key].append({
            "sugerencia_id": sug.pk,
            "codigo": sug.codigo,
            "nombre": sug.nombre,
            "estado": sug.estado,
            "estado_visual": _estado_visual(sug),
            "precio_ref": sug.precio_sugerido,
            "precio_sugerido": sug.precio_sugerido,
            "condicion": sug.condicion_sugerida or CONDICION_BUENA,
            "pieza_creada_id": sug.pieza_creada_id,
        })

    from taller.desarme.catalogo_operativo import get_zonas_orden_desarme
    zonas_orden = get_zonas_orden_desarme(empresa)
    zonas_ordered = [z for z in zonas_orden if z in zonas_dict]
    zonas_ordered.extend(z for z in sorted(zonas_dict) if z not in zonas_ordered)

    zonas = [
        {"key": z, "label": z, "piezas": zonas_dict[z]}
        for z in zonas_ordered
    ]

    total = len(sugerencias)
    pendientes = sum(1 for s in sugerencias if s.estado == SugerenciaPiezaDesarme.PENDIENTE)
    confirmadas = sum(1 for s in sugerencias if s.estado == SugerenciaPiezaDesarme.CONFIRMADA)
    descartadas = sum(1 for s in sugerencias if s.estado == SugerenciaPiezaDesarme.DESCARTADA)
    valor_estimado = sum(
        (s.precio_sugerido or Decimal("0"))
        for s in sugerencias
        if s.estado == SugerenciaPiezaDesarme.CONFIRMADA
    )

    return {
        "vehiculo": vehiculo,
        "zonas": zonas,
        "resumen": {
            "total": total,
            "pendientes": pendientes,
            "confirmadas": confirmadas,
            "descartadas": descartadas,
            "valor_estimado": valor_estimado,
        },
    }


def _empty_resumen() -> dict:
    return {
        "total": 0,
        "pendientes": 0,
        "confirmadas": 0,
        "descartadas": 0,
        "valor_estimado": Decimal("0"),
    }
