from io import StringIO

from django.core.management import call_command

from taller.models.region_ciudad import TallerCiudad, TallerRegion


def ensure_legacy_chile_locations(force: bool = False) -> bool:
    """
    Garantiza que el catálogo legacy de Chile exista.

    Se apoya en el comando `cargar_regiones_ciudades`, que ya conoce las rutas
    JSON y tiene fallback embebido. Retorna True si intentó cargar datos.
    """
    if not force and TallerRegion.objects.exists() and TallerCiudad.objects.exists():
        return False

    stdout = StringIO()
    stderr = StringIO()
    call_command("cargar_regiones_ciudades", stdout=stdout, stderr=stderr, verbosity=0)
    return True
