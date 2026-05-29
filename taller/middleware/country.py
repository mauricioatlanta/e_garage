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
        """Extrae el país del prefijo de la URL (/us/, /cl/, etc.) o del idioma legacy (/en/, /es/)."""
        path = request.path_info or ""
        if path.startswith("/"):
            path_parts = [p for p in path.split("/") if p]
            if path_parts:
                first = path_parts[0].lower()
                # Prefijo de país (ej. /us/en/..., /cl/es/...)
                country_from_prefix = {
                    "us": "US",
                    "cl": "CL",
                    "mx": "MX",
                    "pe": "PE",
                    "co": "CO",
                    "ec": "EC",
                    "ve": "VE",
                    "br": "BR",
                }.get(first)
                if country_from_prefix:
                    return country_from_prefix
                # Legacy: primer segmento como idioma (ej. /en/ → US, /es/ → CL)
                return self.COUNTRY_MAP.get(first)
        return None

    def _get_country_from_user(self, user):
        """Obtiene el país de la configuración del usuario/empresa"""
        try:
            if hasattr(user, "empresa") and user.empresa:
                return getattr(user.empresa, "pais", self.DEFAULT_COUNTRY)
        except:
            pass
        return None
