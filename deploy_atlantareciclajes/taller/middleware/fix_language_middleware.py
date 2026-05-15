"""
Middleware para corregir el idioma basado en el país del usuario
Reemplaza la funcionalidad del CountryLanguageMiddleware
"""

import logging

from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class FixLanguageMiddleware(MiddlewareMixin):
    """
    Middleware que fuerza el idioma correcto según el país del usuario
    - USA: inglés (en)
    - Chile: español (es)
    """

    def process_request(self, request):
        """Procesa el request y establece el idioma correcto"""

        # Determinar país del usuario
        country = None

        # 1. Intentar obtener del usuario autenticado
        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                if hasattr(request.user, "empresa") and request.user.empresa:
                    country = request.user.empresa.pais
                    # Debug logging
                    if getattr(settings, "DEBUG", False):
                        logger.info(
                            f"🌍 FixLanguageMiddleware: Usuario autenticado - {request.user.username}, Empresa: {request.user.empresa.nombre_taller}, País: {country}"
                        )
            except Exception as e:
                if getattr(settings, "DEBUG", False):
                    logger.error(
                        f"🌍 FixLanguageMiddleware: Error obteniendo país del usuario: {e}"
                    )

        # 2. Si no hay usuario, intentar obtener de la URL
        if not country:
            path = request.path or ""
            if path.startswith("/cl/"):
                country = "CL"
            elif path.startswith("/us/"):
                country = "US"

        # 3. Determinar idioma según país
        if country == "US":
            lang = "en"  # Inglés para USA
        elif country == "CL":
            lang = "es"  # Español para Chile
        else:
            lang = "es"  # Fallback a español

        # 4. Activar idioma
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        # Debug logging
        if getattr(settings, "DEBUG", False):
            username = (
                getattr(request.user, "username", "anonymous")
                if hasattr(request, "user")
                else "no_user"
            )
            logger.info(
                f"🌍 FixLanguageMiddleware: country={country}, lang={lang}, user={username}"
            )

        return None

    def process_response(self, request, response):
        """Procesa la respuesta y establece headers correctos"""

        # Establecer Content-Language header
        if hasattr(request, "LANGUAGE_CODE"):
            response.headers["Content-Language"] = request.LANGUAGE_CODE

        # Establecer cookie de idioma correcta
        if hasattr(request, "LANGUAGE_CODE"):
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                request.LANGUAGE_CODE,
                max_age=31536000,
                samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", "Lax"),
                secure=getattr(settings, "LANGUAGE_COOKIE_SECURE", False),
                path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
            )

        return response
