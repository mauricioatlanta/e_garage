"""
Middleware para detectar y configurar el país basado en la URL o configuración del usuario
"""

from django.utils.deprecation import MiddlewareMixin


class CountryMiddleware(MiddlewareMixin):
    """
    Middleware que establece el país actual basado en:
    1. Prefijo de URL (/es/, /en/, etc.)
    2. Configuración del usuario/empresa
    3. Valor por defecto
    """

    COUNTRY_MAP = {
        "es": "CL",  # Español -> Chile
        "en": "US",  # Inglés -> Estados Unidos
        "mx": "MX",  # Español México -> México
    }

    DEFAULT_COUNTRY = "CL"

    def process_request(self, request):
        # 1. Intentar obtener país del prefijo de URL
        country = self._get_country_from_url(request)

        # 2. Si no hay prefijo, intentar obtener del usuario/empresa
        if not country and hasattr(request, "user") and request.user.is_authenticated:
            country = self._get_country_from_user(request.user)

        # 3. Usar valor por defecto
        if not country:
            country = self.DEFAULT_COUNTRY

        # Establecer en request para uso en vistas
        request.country = country

        return None

    def _get_country_from_url(self, request):
        """Extrae el país del prefijo de idioma en la URL"""
        path = request.path_info
        if path.startswith("/"):
            path_parts = path.split("/")
            if len(path_parts) > 1:
                lang_code = path_parts[1]
                return self.COUNTRY_MAP.get(lang_code)
        return None

    def _get_country_from_user(self, user):
        """Obtiene el país de la configuración del usuario/empresa"""
        try:
            if hasattr(user, "empresa") and user.empresa:
                return getattr(user.empresa, "pais", self.DEFAULT_COUNTRY)
        except:
            pass
        return None
