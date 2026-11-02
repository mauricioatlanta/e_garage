"""
Middleware para forzar redirección de rutas /accounts/ a rutas con país.

Evita que usuarios accedan a rutas globales de autenticación sin prefijo de país,
manteniendo la consistencia del sistema multi-país SaaS.
"""

import logging
from urllib.parse import urlencode

from django.shortcuts import redirect

from taller.utils.empresa import get_user_empresa_safe

logger = logging.getLogger(__name__)


class AccountsCountryRedirectMiddleware:
    """
    Fuerza que todas las rutas /accounts/* se redirijan a rutas con prefijo de país.

    Ejemplos:
    - /accounts/login/ → /cl/es/accounts/login/ (país por defecto)
    - /accounts/password/reset/ → /cl/es/accounts/password/reset/
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path.startswith("/accounts/"):
            if not (path.startswith("/cl/") or path.startswith("/us/") or path.startswith("/br/")):
                default_country = self._get_default_country(request)
                new_path = f"/{default_country}/es{path}"

                if request.GET:
                    new_path += "?" + urlencode(request.GET, doseq=True)

                logger.info("Redirigiendo ruta de autenticación: %s → %s", path, new_path)
                return redirect(new_path)

        return self.get_response(request)

    def _get_default_country(self, request):
        country_param = request.GET.get("country", "").lower()
        if country_param in ["cl", "us", "br"]:
            return country_param

        country_cookie = request.COOKIES.get("country", "").lower()
        if country_cookie in ["cl", "us", "br"]:
            return country_cookie

        if request.user.is_authenticated:
            try:
                empresa = get_user_empresa_safe(request.user)
                pais = (getattr(empresa, "pais", "") or "").upper()
                if pais == "CL":
                    return "cl"
                if pais == "US":
                    return "us"
                if pais == "BR":
                    return "br"
            except Exception as e:
                logger.warning("Error obteniendo país de empresa: %s", e)

        return "cl"
