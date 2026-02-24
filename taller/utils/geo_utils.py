"""
Utilidades geográficas para normalización de códigos de país.

Este módulo contiene funciones puras para trabajar con códigos de país,
sin dependencias de Django o modelos. Puede ser usado en cualquier parte
del proyecto sin necesidad de instanciar middlewares o clases.
"""


def normalize_country_code(country_code):
    """
    Normaliza códigos de país a formato estándar ISO 3166-1 alpha-2.
    
    Esta función convierte variaciones comunes de códigos de país (como "USA", "CHILE", etc.)
    a su formato estándar de dos letras (US, CL, etc.).
    
    Args:
        country_code: Código de país en cualquier formato (str, int, None, etc.)
    
    Returns:
        str: Código de país normalizado en formato ISO 3166-1 alpha-2.
             Si el código es None o vacío, retorna 'CL' (Chile) como valor por defecto.
    
    Ejemplos:
        >>> normalize_country_code("USA")
        'US'
        >>> normalize_country_code("chile")
        'CL'
        >>> normalize_country_code("MX")
        'MX'
        >>> normalize_country_code("BRASIL")
        'BR'
        >>> normalize_country_code(None)
        'CL'
        >>> normalize_country_code("")
        'CL'
    """
    # Manejar valores None o vacíos
    if not country_code:
        return 'CL'  # País por defecto
    
    # Convertir a string, normalizar y limpiar
    country_code = str(country_code).upper().strip()
    
    # Si después de limpiar está vacío, retornar default
    if not country_code:
        return 'CL'
    
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



