SUPPORTED_COUNTRY_PREFIXES = {"cl", "us", "uy", "ar", "br", "pe", "mx", "co", "ec", "ve"}
COUNTRY_ALIASES = {
    "chile": "cl",
    "cl": "cl",
    "usa": "us",
    "us": "us",
    "eeuu": "us",
    "estados_unidos": "us",
    "united_states": "us",
    "uruguay": "uy",
    "uy": "uy",
    "argentina": "ar",
    "ar": "ar",
    "brasil": "br",
    "brazil": "br",
    "br": "br",
    "peru": "pe",
    "pe": "pe",
    "mexico": "mx",
    "mx": "mx",
    "colombia": "co",
    "co": "co",
    "ecuador": "ec",
    "ec": "ec",
    "venezuela": "ve",
    "ve": "ve",
}


# Códigos de idioma típicos en rutas (2 letras)
COMMON_LANG_CODES = {"en", "es", "pt"}


def prefix_from_path(path: str) -> str:
    """
    Extrae el prefijo país+idioma desde rutas como /cl/es/... o /us/en/...
    Devuelve "cl/es", "us/en", etc., para que login y next conserven país e idioma.
    Si solo hay país en la ruta, devuelve solo el código de país (ej. "cl").
    """
    if not path:
        return ""

    parts = [p.strip().lower() for p in path.strip("/").split("/") if p.strip()]
    if not parts:
        return ""

    first = parts[0]
    if first not in SUPPORTED_COUNTRY_PREFIXES:
        return ""

    # Si hay segundo segmento que parece idioma (2 letras, conocido), devolver país/idioma
    if len(parts) >= 2:
        second = parts[1]
        if len(second) == 2 and (second in COMMON_LANG_CODES or second.isalpha()):
            return f"{first}/{second}"

    return first


def get_normalized_country(value: str | None) -> str:
    """
    Normaliza nombres/códigos de país a prefijos cortos usados por eGarage.
    """
    if not value:
        return "cl"

    key = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return COUNTRY_ALIASES.get(key, key if key in SUPPORTED_COUNTRY_PREFIXES else "cl")
