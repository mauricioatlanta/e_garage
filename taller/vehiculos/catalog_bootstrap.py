import logging
from io import StringIO

from django.core.management import call_command

from taller.models.marca import Marca
from taller.models.modelo import Modelo

log = logging.getLogger(__name__)


def ensure_vehicle_catalog_for_country(country: str) -> bool:
    """
    Populate the vehicle catalog for a country when it is completely or mostly empty.

    Returns True when a bootstrap was attempted.
    """
    country = (country or "").strip().upper()

    if country != "CL":
        return False

    has_marcas = Marca.objects.filter(country=country).exists()
    has_modelos = Modelo.objects.filter(country=country).exists()

    if has_marcas and has_modelos:
        return False

    log.warning(
        "[ensure_vehicle_catalog_for_country] Catalogo %s incompleto. "
        "Disparando carga idempotente de marcas/modelos.",
        country,
    )

    try:
        call_command(
            "cargar_marcas_modelos_por_pais",
            country=country,
            verbosity=0,
            stdout=StringIO(),
            stderr=StringIO(),
        )
        return True
    except Exception:
        log.exception(
            "[ensure_vehicle_catalog_for_country] Error cargando catalogo de vehiculos para %s",
            country,
        )
        return False
