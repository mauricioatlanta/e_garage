from io import StringIO

from django.core.management import call_command

from taller.models.ubicacion import Ciudad, Estado


def ensure_usa_locations() -> bool:
    """Garantiza que el catálogo de estados y ciudades de USA esté cargado."""
    if Estado.objects.filter(pais="US").exists() and Ciudad.objects.filter(
        estado__pais="US"
    ).exists():
        return False

    output = StringIO()
    call_command("cargar_estados_usa", stdout=output, stderr=output, verbosity=0)

    if not Estado.objects.filter(pais="US").exists() or not Ciudad.objects.filter(
        estado__pais="US"
    ).exists():
        raise RuntimeError(
            "No se pudo cargar el catálogo de estados y ciudades de USA. "
            f"{output.getvalue().strip()}"
        )
    return True
