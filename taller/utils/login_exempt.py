"""
Helper común para rutas de login exentas (multi-país).
Normaliza /{country}/{lang}/... a ruta base para comparar una sola lista.

Uso en middlewares (empresa, suscripción, tenant) para no duplicar listas
/cl/es/accounts/login/, /us/en/accounts/login/, etc.
"""

from __future__ import annotations

# Códigos de país e idioma en path (2 letras)
_PATH_COUNTRY_LEN = 2
_PATH_LANGS = ("es", "en", "pt")


def strip_country_locale_prefix(path: str) -> str:
    """
    Quita prefijo /<cc>/<lang>/ del path.
    /cl/es/accounts/login/ -> /accounts/login/
    /us/en/accounts/login/ -> /accounts/login/
    /accounts/login/       -> /accounts/login/
    """
    path = (path or "").strip().rstrip("/") or "/"
    parts = [p for p in path.split("/") if p]
    if len(parts) < 3:
        return path if path.startswith("/") else "/" + path
    first, second = parts[0], parts[1]
    if len(first) == _PATH_COUNTRY_LEN and second.lower() in _PATH_LANGS:
        rest = "/" + "/".join(parts[2:])
        return rest
    return path if path.startswith("/") else "/" + path


# Lista mínima de rutas base de login (sin prefijo país/idioma)
LOGIN_EXEMPT_BASE_PATHS = (
    "/accounts/login/",
    "/account/login/",
)


def is_login_exempt_path(path: str) -> bool:
    """
    True si la ruta es de login (con o sin prefijo /cc/lang/, con o sin barra final).
    Usar en middlewares para exentar GET/POST login sin mantener listas sueltas.
    """
    norm = strip_country_locale_prefix(path)
    norm = (norm or "").rstrip("/") + "/"
    return any(norm.startswith(base) for base in LOGIN_EXEMPT_BASE_PATHS)
