"""
Utilidades generales para el sistema eGarage.

Este módulo contiene funciones de utilidad que pueden ser usadas
en cualquier parte del proyecto sin dependencias complejas.
"""


def get_normalized_country(country_code):
    """
    Toma un código de país y lo devuelve en formato estándar (ej: 'cl' -> 'CL').
    Si no hay código, devuelve el valor por defecto 'CL'.

    Esta función normaliza códigos de país a formato estándar ISO 3166-1 alpha-2.
    Convierte variaciones comunes (como "USA", "CHILE", etc.) a su formato estándar.

    Args:
        country_code: Código de país en cualquier formato (str, int, None, etc.)

    Returns:
        str: Código de país normalizado en formato ISO 3166-1 alpha-2.
             Si el código es None o vacío, retorna 'CL' (Chile) como valor por defecto.

    Ejemplos:
        >>> get_normalized_country("USA")
        'US'
        >>> get_normalized_country("chile")
        'CL'
        >>> get_normalized_country("MX")
        'MX'
        >>> get_normalized_country(None)
        'CL'
        >>> get_normalized_country("")
        'CL'
    """
    # Manejar valores None o vacíos
    if not country_code:
        return "CL"  # País por defecto

    # Convertir a string, normalizar y limpiar
    country_code = str(country_code).strip().upper()

    # Si después de limpiar está vacío, retornar default
    if not country_code:
        return "CL"

    # Mapeo de códigos comunes a formato estándar ISO 3166-1 alpha-2
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

    # Retornar el código normalizado o el original si no está en el mapeo
    return country_map.get(country_code, country_code)


def get_country_from_request(request, default="CL"):
    """
    Detecta el país desde el REQUEST. Prioridad: prefijo de URL > request.country > empresa > default.

    IMPORTANTE: No usar el host/dominio. En egarage.cl tanto /us/ como /cl/ pueden existir.
    La fuente de verdad es el prefijo de path: /us/ → US, /cl/ → CL, etc.

    Args:
        request: HttpRequest
        default: País por defecto si no se puede detectar

    Returns:
        str: Código de país en mayúsculas (US, CL, PE, BR, MX, etc.)
    """
    path = (request.path or "").lower()

    # 1) Prefijo explícito en path manda (no usar host)
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

    # 2) request.country (seteado por CountryDetectionMiddleware)
    raw = getattr(request, "country", None) or getattr(request, "country_code", None)

    # 3) empresa.pais como fallback
    if not raw:
        empresa = getattr(request.user, "empresa", None) if hasattr(request, "user") else None
        raw = getattr(empresa, "pais", None) if empresa else None

    c = str(raw or default).strip().upper()
    return get_normalized_country(c) if c else default
