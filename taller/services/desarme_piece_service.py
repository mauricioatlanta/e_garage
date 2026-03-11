"""
Servicio para piezas del mapa de desarme.
Crear/actualizar pieza por zona con transacción atómica.
"""

from decimal import Decimal
from typing import Optional, Dict, Any, Tuple

from django.db import transaction

from taller.models import Repuesto, Vehiculo
from taller.services.desarme_kpis import STATUS_TO_BACKEND, STATUS_TO_FRONTEND


def _piece_to_frontend(pieza: Repuesto) -> Dict[str, Any]:
    """Convierte un Repuesto a formato frontend."""
    status = (pieza.estado_pieza or "").strip()
    status_front = STATUS_TO_FRONTEND.get(status, "unreviewed")
    return {
        "id": pieza.id,
        "piece_name": pieza.nombre,
        "status": status_front,
        "price": str(pieza.precio_venta or "0"),
        "stock": pieza.cantidad_stock or 1,
        "note": (getattr(pieza, "observaciones", None) or "")[:500],
        "zone": pieza.zona_mapa or "",
        "view": pieza.vista_mapa or "",
    }


def get_piece_by_zone(vehiculo: Vehiculo, zone: str, view: str) -> Optional[Repuesto]:
    """
    Obtiene la pieza para una zona/vista.
    Regla: tipo_origen=desarme, vehiculo_origen=vehiculo.
    """
    qs = vehiculo.repuestos_desarme.filter(zona_mapa=zone)
    if view:
        qs = qs.filter(vista_mapa=view)
    return qs.first()


@transaction.atomic
def create_or_update_piece(
    vehiculo: Vehiculo,
    zone: str,
    view: str,
    piece_name: str,
    estado_pieza: str = "disponible",
    precio_venta: str = "0",
    stock: int = 1,
    observacion_estado: str = "",
) -> Tuple[Repuesto, Dict, Dict]:
    """
    Crea o actualiza una pieza por zona.
    Reglas:
    - tipo_origen=desarme, vehiculo_origen=vehiculo, empresa=vehiculo.empresa
    - es_usado=True
    - Transacción atómica
    Retorna (pieza, summary, kpis).
    """
    from taller.services.desarme_kpis import get_kpis, get_piece_summary

    if vehiculo.estado_desarme == "cerrado":
        raise ValueError("Vehículo cerrado, no se pueden modificar piezas.")

    estado_backend = STATUS_TO_BACKEND.get(estado_pieza, "disponible")
    if estado_backend not in ("disponible", "dañado", "scrap", "vendido", "reservada"):
        estado_backend = "disponible"

    try:
        precio = Decimal(str(precio_venta).replace(",", ".")) if precio_venta else Decimal("0")
    except Exception:
        precio = Decimal("0")
    stock_val = max(0, int(stock) if stock is not None else 1)
    obs = (observacion_estado or "").strip()[:500]

    pieza = get_piece_by_zone(vehiculo, zone, view)
    if not pieza:
        pieza = Repuesto(
            empresa=vehiculo.empresa,
            nombre=piece_name,
            tipo_origen="desarme",
            vehiculo_origen=vehiculo,
            es_usado=True,
            controlar_stock=True,
            cantidad_stock=stock_val,
            origen_costo="desarme",
            zona_mapa=zone,
            vista_mapa=view,
        )
    pieza.nombre = piece_name
    pieza.estado_pieza = estado_backend
    pieza.precio_venta = precio
    pieza.cantidad_stock = stock_val
    if hasattr(pieza, "observaciones"):
        pieza.observaciones = obs
    pieza.save()

    summary = get_piece_summary(vehiculo)
    kpis = get_kpis(vehiculo)
    return pieza, summary, kpis
