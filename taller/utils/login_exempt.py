"""
Helper común para rutas que no requieren login.

Usado por middleware (verificar_suscripcion, empresa_middleware, tenant_isolation)
para decidir si una ruta está exenta de verificación de autenticación/suscripción.
"""

# Prefijos de ruta que no requieren login (signup, login, logout, static, etc.)
# Se chequea tanto path raw como path sin prefijo país/idioma (ej. /us/accounts/ -> /accounts/)
LOGIN_EXEMPT_PREFIXES = frozenset(
    [
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/signup/",
        "/accounts/password/",
        "/login/",
        "/logout/",
        "/signup/",
        "/registro/",
        "/registro-trial/",
        "/static/",
        "/media/",
        "/favicon.ico",
        "/robots.txt",
        "/health/",
        "/health-simple/",
        "/jsi18n/",
        "/i18n/",
        "/lang/",
        "/legal/",
        "/precios/",
        "/portal/",
        "/suscripcion-bloqueada/",
        "/suspension/",
        "/contacto-ventas/",
        "/verificar-docs/",
    ]
)


def _strip_country_locale(path: str) -> str:
    """
    Quita prefijo país/idioma:
    /us/es/accounts/login/ -> /accounts/login/
    /us/accounts/login/ -> /accounts/login/
    """
    parts = [p for p in path.split("/") if p]
    if not parts:
        return path
    # Strip country (2-char)
    if len(parts[0]) == 2:
        parts = parts[1:]
    if not parts:
        return "/"
    # Strip language (2-char)
    if len(parts[0]) == 2:
        parts = parts[1:]
    return "/" + "/".join(parts) if parts else "/"


def is_login_exempt_path(path: str) -> bool:
    """
    Retorna True si la ruta no requiere autenticación.
    Usado para exentar rutas del middleware de suscripción y empresa.
    Soporta rutas con prefijo país (ej. /us/accounts/login/).
    """
    if not path or not isinstance(path, str):
        return False
    path = path.strip()
    if path in ("/", ""):
        return True
    path_norm = path if path.startswith("/") else f"/{path}"
    if any(path_norm.startswith(p) for p in LOGIN_EXEMPT_PREFIXES):
        return True
    path_stripped = _strip_country_locale(path_norm)
    return any(path_stripped.startswith(p) for p in LOGIN_EXEMPT_PREFIXES)
