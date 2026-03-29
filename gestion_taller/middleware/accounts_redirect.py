"""
Middleware para forzar redirección de rutas /accounts/ a rutas con país.

Evita que usuarios accedan a rutas globales de autenticación sin prefijo de país,
manteniendo la consistencia del sistema multi-país SaaS.
"""

import logging
from django.shortcuts import redirect
from django.conf import settings

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

        # Si la ruta empieza con /accounts/ pero NO tiene prefijo de país
        if path.startswith("/accounts/"):
            # Verificar que no tenga ya un prefijo de país
            if not (path.startswith("/cl/") or path.startswith("/us/") or path.startswith("/br/")):
                # Determinar país por defecto
                default_country = self._get_default_country(request)

                # Construir nueva ruta con prefijo de país
                new_path = f"/{default_country}/es{path}"

                # Preservar query string
                if request.GET:
                    from urllib.parse import urlencode

                    new_path += "?" + urlencode(request.GET, doseq=True)

                logger.info(f"Redirigiendo ruta de autenticación: {path} → {new_path}")
                return redirect(new_path)

        return self.get_response(request)

    def _get_default_country(self, request):
        """
        Determina el país por defecto basado en:
        1. Parámetro 'country' en query string
        2. Cookie de país
        3. Usuario autenticado y su empresa
        4. Default: 'cl'
        """
        # 1. Query string
        country_param = request.GET.get("country", "").lower()
        if country_param in ["cl", "us", "br"]:
            return country_param

        # 2. Cookie
        country_cookie = request.COOKIES.get("country", "").lower()
        if country_cookie in ["cl", "us", "br"]:
            return country_cookie

        # 3. Usuario autenticado
        if request.user.is_authenticated:
            try:
                from taller.utils.empresa import get_or_create_empresa

                empresa = get_or_create_empresa(request)
                pais = (getattr(empresa, "pais", "") or "").upper()
                if pais == "CL":
                    return "cl"
                elif pais == "US":
                    return "us"
                elif pais == "BR":
                    return "br"
            except Exception as e:
                logger.warning(f"Error obteniendo país de empresa: {e}")

        # 4. Default
        return "cl"
