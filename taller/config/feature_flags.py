"""
Helper central para obtener features por país.
Devuelve dict independiente (deepcopy) con fallback a CL.
"""

from copy import deepcopy

from .country_features import COUNTRY_FEATURES

DEFAULT_COUNTRY = "CL"


def get_country_features(country_code: str | None) -> dict:
    """
    Obtiene features del país. Normaliza a uppercase, mezcla defaults de CL
    con el país solicitado, devuelve copia independiente. Incluye 'country'.
    """
    base = deepcopy(COUNTRY_FEATURES.get(DEFAULT_COUNTRY, {}))
    code = (country_code or "").strip().upper() if country_code else ""
    if not code or code not in COUNTRY_FEATURES:
        code = DEFAULT_COUNTRY
    overlay = COUNTRY_FEATURES.get(code, base)
    result = deepcopy(base)
    for k, v in overlay.items():
        result[k] = v
    result["country"] = code
    return result
