# taller/utils/country.py

SUPPORTED_COUNTRIES = {"cl", "us"}  # luego agregas "pe", "co", etc.


def get_normalized_country(country_code):
    """
    Normaliza código de país a formato ISO 3166-1 alpha-2 (ej: 'cl' -> 'CL').
    """
    if not country_code:
        return "CL"
    country_code = str(country_code).strip().upper()
    if not country_code:
        return "CL"
    country_map = {
        "US": "US",
        "USA": "US",
        "UNITED STATES": "US",
        "CL": "CL",
        "CHILE": "CL",
        "MX": "MX",
        "MEXICO": "MX",
        "MEX": "MX",
        "CO": "CO",
        "COLOMBIA": "CO",
        "EC": "EC",
        "ECUADOR": "EC",
        "PE": "PE",
        "PERU": "PE",
        "PERÚ": "PE",
        "VE": "VE",
        "VENEZUELA": "VE",
        "BR": "BR",
        "BRASIL": "BR",
        "BRAZIL": "BR",
        "AR": "AR",
        "ARGENTINA": "AR",
        "UY": "UY",
        "URUGUAY": "UY",
    }
    return country_map.get(country_code, country_code)


def get_country_from_request(request, default="CL"):
    """
    Detecta país desde path primero (/us/ -> US), luego request.country, empresa.
    """
    path = (request.path or "").lower()
    if path.startswith("/us/"):
        return "US"
    if path.startswith("/cl/"):
        return "CL"
    if path.startswith("/pe/"):
        return "PE"
    if path.startswith("/br/"):
        return "BR"
    if path.startswith("/mx/"):
        return "MX"
    if path.startswith("/co/"):
        return "CO"
    if path.startswith("/ec/"):
        return "EC"
    if path.startswith("/ve/"):
        return "VE"
    if path.startswith("/ar/"):
        return "AR"
    if path.startswith("/uy/"):
        return "UY"
    raw = getattr(request, "country", None) or getattr(request, "country_code", None)
    if not raw:
        empresa = getattr(request.user, "empresa", None) if hasattr(request, "user") else None
        raw = getattr(empresa, "pais", None) if empresa else None
    c = str(raw or default).strip().upper()
    return get_normalized_country(c) if c else default


SUPPORTED_LANGS = {"es", "en"}  # ajustable


def country_from_path(path: str) -> str:
    parts = (path or "/").lstrip("/").split("/")
    if parts and parts[0] in SUPPORTED_COUNTRIES:
        return parts[0]
    return "cl"


def prefix_from_path(path: str) -> str:
    """
    Devuelve el prefijo que realmente usa tu routing:
    - /cl/es/... -> "cl/es"
    - /us/en/... -> "us/en"
    - /us/...    -> "us"
    - /cl/...    -> "cl"
    """
    parts = (path or "/").lstrip("/").split("/")
    if not parts:
        return "cl"

    cc = parts[0]
    if cc not in SUPPORTED_COUNTRIES:
        return "cl"

    if len(parts) >= 2 and parts[1] in SUPPORTED_LANGS:
        return f"{cc}/{parts[1]}"

    return cc
