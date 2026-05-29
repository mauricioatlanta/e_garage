# taller/context_processors/ui_labels.py

from taller.config.ui_labels import get_ui_labels


# Mapa entre prefijos de URL y códigos de país usados en el sistema
URL_PREFIX_TO_COUNTRY = {
    "cl": "CL",
    "us": "US",
    "mx": "MX",
    "pe": "PE",
    "co": "CO",
    "ar": "AR",
    "br": "BR",
    "ec": "EC",
    "ve": "VE",
    "uy": "UY",
}


def _get_country_from_path(path):
    """
    Dado un path como '/cl/es/documentos/lista/',
    retorna el código de país en MAYÚSCULA (por ejemplo 'CL').

    Si no se puede determinar, usa CL por defecto.
    """
    if not path:
        return "CL"

    # Quita slashes iniciales/finales y toma el primer segmento
    parts = path.strip("/").split("/")
    if not parts:
        return "CL"

    prefix = parts[0].lower()
    return URL_PREFIX_TO_COUNTRY.get(prefix, "CL")


def ui_labels_context(request):
    """
    Context processor que inyecta 'ui_labels' en todas las plantillas.

    Usa:
    - el prefijo de la URL para inferir el país (cl, us, mx, etc.)
    - request.LANGUAGE_CODE (si está disponible) para el idioma
    """
    path = request.path or "/"
    country_code = _get_country_from_path(path)

    language_code = getattr(request, "LANGUAGE_CODE", None)
    labels = get_ui_labels(country_code=country_code, language_code=language_code)

    return {
        "ui_labels": labels,
        "ui_country_code": country_code,
    }
