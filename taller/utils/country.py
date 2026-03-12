SUPPORTED_COUNTRY_PREFIXES = {"cl", "us", "uy", "ar", "br", "pe", "mx"}


def prefix_from_path(path: str) -> str:
    """
    Extrae el prefijo país desde rutas como:
    /cl/es/..., /us/en/..., /uy/es/...
    Retorna '' si no encuentra un prefijo válido.
    """
    if not path:
        return ""

    parts = [p.strip().lower() for p in path.strip("/").split("/") if p.strip()]
    if not parts:
        return ""

    first = parts[0]
    return first if first in SUPPORTED_COUNTRY_PREFIXES else ""
