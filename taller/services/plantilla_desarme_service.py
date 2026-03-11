"""
Servicio de plantillas de desarme: generación automática de piezas desde plantilla.
"""

import logging
from typing import List

from django.db import transaction
from django.core.exceptions import ValidationError

from taller.models import Repuesto, Vehiculo
from taller.models.plantilla_desarme import PlantillaDesarme, PlantillaPieza

log = logging.getLogger(__name__)


class PlantillaDesarmeError(ValidationError):
    """Error al aplicar plantilla de desarme."""

    pass


@transaction.atomic
def aplicar_plantilla(vehiculo: Vehiculo, plantilla: PlantillaDesarme) -> List[Repuesto]:
    """
    Genera repuestos de desarme desde una plantilla para el vehículo dado.

    Reglas:
    - Multi-tenant: plantilla.empresa == vehiculo.empresa OR plantilla.empresa is NULL
    - No duplicar: bloquea si ya existen piezas de desarme para este vehículo
    - Transacción atómica
    - Usa cantidad_stock=1, tipo_origen="desarme", vehiculo_origen=vehiculo

    Args:
        vehiculo: Vehículo de desarme destino
        plantilla: Plantilla a aplicar

    Returns:
        Lista de repuestos creados

    Raises:
        PlantillaDesarmeError: si falla validación multi-tenant o duplicados
    """
    # Validación multi-tenant: plantilla debe ser global o del mismo tenant
    if plantilla.empresa_id is not None and plantilla.empresa_id != vehiculo.empresa_id:
        raise PlantillaDesarmeError(
            "La plantilla no pertenece a tu empresa o no es una plantilla global."
        )

    # Validación: no duplicar piezas del mismo vehículo
    if Repuesto.objects.filter(vehiculo_origen=vehiculo, tipo_origen="desarme").exists():
        raise PlantillaDesarmeError(
            f"El vehículo ya tiene piezas de desarme. "
            f"No se puede aplicar otra plantilla para evitar duplicados. "
            f"Use el checklist para inspeccionar las piezas existentes."
        )

    if vehiculo.tipo_uso != "desarme":
        raise PlantillaDesarmeError("El vehículo debe ser tipo 'desarme' para aplicar plantillas.")

    if (vehiculo.estado_desarme or "").strip() == "cerrado":
        raise PlantillaDesarmeError("El vehículo está cerrado. No se pueden agregar piezas.")

    if not plantilla.activa:
        raise PlantillaDesarmeError(f"La plantilla '{plantilla.nombre}' no está activa.")

    piezas = list(plantilla.piezas.filter(activo=True).order_by("orden", "id"))
    if not piezas:
        raise PlantillaDesarmeError(f"La plantilla '{plantilla.nombre}' no tiene piezas activas.")

    repuestos = []
    empresa = vehiculo.empresa
    for pieza in piezas:
        # Categoría solo si pertenece al mismo tenant
        categoria = None
        if pieza.categoria_id and pieza.categoria.empresa_id == empresa.id:
            categoria = pieza.categoria
        zona = getattr(pieza, "zona_mapa", None) or ""
        vista = getattr(pieza, "vista_mapa", None) or ""
        repuesto = Repuesto.objects.create(
            empresa=empresa,
            nombre=pieza.nombre_pieza,
            part_number=pieza.codigo_base or None,
            categoria=categoria,
            tipo_origen="desarme",
            vehiculo_origen=vehiculo,
            es_usado=True,
            controlar_stock=True,
            cantidad_stock=1,
            estado_pieza="",  # unreviewed (checklist pendiente)
            origen_costo="desarme",
            precio_compra=0,
            precio_venta=0,
            zona_mapa=zona[:60] if zona else "",
            vista_mapa=vista[:30] if vista else "",
        )
        repuestos.append(repuesto)
        log.debug(f"  Creado: {repuesto.nombre}")

    log.info(
        f"[PlantillaDesarme] Aplicada '{plantilla.nombre}' a vehículo {vehiculo.pk}: "
        f"{len(repuestos)} piezas creadas"
    )
    return repuestos


def plantillas_disponibles_para(empresa) -> List[PlantillaDesarme]:
    """
    Devuelve plantillas que puede usar una empresa:
    globales (empresa=null) + propias (empresa=empresa).
    """
    from django.db.models import Q

    return list(
        PlantillaDesarme.objects.filter(activa=True)
        .filter(Q(empresa__isnull=True) | Q(empresa=empresa))
        .order_by("nombre")
    )
