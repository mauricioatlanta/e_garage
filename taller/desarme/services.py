"""
Servicios del módulo Desarme.
El catálogo usado depende del país de la empresa: USA → catálogo USA; resto → legacy.
"""

from taller.models.pieza_desarme import PiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo


def _ensure_vehiculo_desarme(vehiculo, empresa=None):
    if isinstance(vehiculo, VehiculoDesarme):
        return vehiculo

    if not isinstance(vehiculo, Vehiculo):
        raise ValueError("vehiculo debe ser Vehiculo o VehiculoDesarme")

    if vehiculo.tipo_uso != Vehiculo.TIPO_USO_DESARME:
        raise ValueError("Legacy Vehiculo debe tener tipo_uso=DESARME")

    empresa = empresa or getattr(vehiculo, "empresa", None)
    qs = VehiculoDesarme.objects.filter(vehiculo_origen_id=vehiculo.pk)
    if empresa is not None:
        qs = qs.filter(empresa=empresa)

    vehiculo_desarme = qs.first()
    if vehiculo_desarme is not None:
        return vehiculo_desarme

    raise ValueError(
        f"No existe VehiculoDesarme para el Vehiculo legacy id={vehiculo.pk}. "
        "Asegura que la migración creó el registro correspondiente."
    )


def puede_eliminar_pieza(pieza) -> tuple[bool, str]:
    """
    Determines whether a PiezaDesarme can be safely deleted.
    Returns (can_delete, reason_if_blocked).

    Blocking conditions:
    - publicada=True (live in storefront)
    - has LineaRepuesto (PROTECT — referenced by document lines)
    - has LineaVentaDesarme (direct sales)
    - has MovimientoInventario (PROTECT — inventory movements)
    """
    if pieza.publicada:
        return False, "La pieza está publicada en el kiosko. Despublícala primero."
    if pieza.lineas_repuesto.exists():
        return False, "La pieza tiene líneas de documento asociadas y no puede eliminarse."
    if pieza.lineas_venta_desarme.exists():
        return False, "La pieza tiene ventas registradas y no puede eliminarse."
    if pieza.movimientos_inventario.exists():
        return False, "La pieza tiene movimientos de inventario y no puede eliminarse."
    return True, ""


def inicializar_sugerencias(vehiculo, empresa) -> int:
    """
    Crea SugerenciaPiezaDesarme PENDIENTE para cada pieza del catálogo sugerido
    según el tipo_carroceria del vehículo. Idempotente: get_or_create no duplica.
    Retorna el número de sugerencias nuevas creadas.
    """
    if isinstance(vehiculo, Vehiculo) and vehiculo.tipo_uso != Vehiculo.TIPO_USO_DESARME:
        return 0

    from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
    from .catalogo_operativo import get_catalogo_para_vehiculo

    vehiculo = _ensure_vehiculo_desarme(vehiculo, empresa)
    catalogo = get_catalogo_para_vehiculo(empresa, vehiculo)
    count = 0
    for item in catalogo:
        _, created = SugerenciaPiezaDesarme.objects.get_or_create(
            vehiculo_desarme=vehiculo,
            codigo=item["codigo"],
            defaults={
                "empresa": empresa,
                "nombre": item["nombre"],
                "zona": item["zona"],
                "precio_sugerido": item["precio_base"],
                "estado": SugerenciaPiezaDesarme.PENDIENTE,
            },
        )
        if created:
            count += 1
    return count
