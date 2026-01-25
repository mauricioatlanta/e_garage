"""
Middleware para detectar y configurar el país e idioma basado en:
1. Query parameter (country=CL, country=US, etc.)
2. URL path (/cl/, /us/, etc.)
3. Sesión guardada
4. Usuario autenticado/empresa
5. Valor por defecto

También activa el idioma correspondiente al país detectado.
"""

from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import activate
from taller.utils import get_normalized_country


class CountryDetectionMiddleware(MiddlewareMixin):
    """
    Middleware que establece el país actual y activa el idioma correspondiente.
    Debe ejecutarse después de SessionMiddleware pero antes de LocaleMiddleware.
    """

    DEFAULT_COUNTRY = "CL"

    # Mapeo de idiomas por país
    # Nota: Django usa códigos con guión bajo para archivos (pt_BR), pero acepta pt-br en LANGUAGES
    COUNTRY_LANGUAGE_MAP = {
        "BR": "pt-br",  # Brasil -> Portugués (Django lo convierte internamente a pt_BR)
        "US": "en",  # USA -> Inglés
        # Todos estos usan Español
        "CL": "es",
        "MX": "es",
        "CO": "es",
        "AR": "es",
        "PE": "es",
        "VE": "es",
        "EC": "es",
        "UY": "es",
    }

    def process_request(self, request):
        """
        Detecta el país desde múltiples fuentes, establece request.country
        y activa el idioma correspondiente.
        """
        country = None

        # 1. Query parameter (prioridad más alta)
        country_param = request.GET.get("country", "").upper().strip()
        if country_param:
            country = get_normalized_country(country_param)

        # 2. URL path (/cl/, /us/, etc.)
        if not country:
            country = self._get_country_from_url(request.path)

        # 3. Sesión guardada
        if not country:
            saved_country = request.session.get("preferred_country", "").upper().strip()
            if saved_country:
                country = get_normalized_country(saved_country)

        # 4. Usuario autenticado/empresa
        if not country and hasattr(request, "user") and request.user.is_authenticated:
            country = self._get_country_from_user(request.user)

        # 5. Valor por defecto
        if not country:
            country = self.DEFAULT_COUNTRY

        # Obtener el idioma correspondiente al país (fallback a español)
        lang = self.COUNTRY_LANGUAGE_MAP.get(country, "es")

        # Establecer en request para uso en vistas y context processors
        request.country = country
        request.country_code = country

        # Guardar en sesión para futuras requests
        request.session["preferred_country"] = country
        request.session["django_language"] = lang

        # Activar el idioma para esta request (DEBE hacerse ANTES de LocaleMiddleware)
        activate(lang)

        # CRÍTICO: Si hay parámetro GET country, forzar el idioma y sobrescribir cookies
        # Esto previene que LocaleMiddleware use la cookie antigua
        country_param = request.GET.get("country", "").upper().strip()
        if country_param:
            # Forzar activación del idioma correcto
            activate(lang)
            # Establecer en request para que otros middlewares lo respeten
            request.LANGUAGE_CODE = lang
            print(
                f"[CountryDetectionMiddleware] GET param detected - Forcing language: {lang} for country: {country}"
            )

        # Debug logging
        print(f"[CountryDetectionMiddleware] Detected country: {country}, Language: {lang}")

        return None

    def _get_country_from_url(self, path):
        """Extrae el país del prefijo de país en la URL"""
        if not path:
            return None

        path_lower = path.lower().strip("/")
        path_parts = path_lower.split("/")

        # Buscar código de país en las primeras partes del path
        if path_parts:
            first_part = path_parts[0]
            country = get_normalized_country(first_part)
            # Si se normalizó correctamente, retornarlo
            if country and country != first_part.upper():
                return country
            # Si es un código válido directamente
            if first_part.upper() in ["US", "CL", "MX", "CO", "EC", "PE", "VE", "BR", "AR", "UY"]:
                return first_part.upper()

        return None

    def _get_country_from_user(self, user):
        """Obtiene el país de la configuración del usuario/empresa"""
        try:
            # Intentar desde empresa
            if hasattr(user, "empresa") and user.empresa:
                empresa_country = getattr(user.empresa, "pais", None)
                if empresa_country:
                    return get_normalized_country(empresa_country)

            # Intentar desde perfil
            if hasattr(user, "perfil") and user.perfil:
                perfil_country = getattr(user.perfil, "pais", None)
                if perfil_country:
                    return get_normalized_country(perfil_country)
        except Exception:
            pass

        return None
