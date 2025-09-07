"""
Middleware para detectar contexto de país desde URL
Siguiendo la jerarquía recomendada:
1. Prefijo de URL: /us/ o /cl/
2. Subdominio: us.egarage.com o cl.egarage.com
3. Perfil de organización (tenant)
4. Dirección fiscal/Sucursal principal
5. Último recurso: geolocalización de IP

NUEVA FUNCIONALIDAD: Redirección automática cuando hay conflicto entre URL y empresa
"""

import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin


class CountryContextMiddleware(MiddlewareMixin):
    """
    Middleware que detecta el país del contexto actual y lo coloca en request.country

    Jerarquía de detección:
    1. URL prefix: /us/ → US, /cl/ → CL
    2. Subdominio: us.domain.com → US, cl.domain.com → CL
    3. Usuario/empresa configuración
    4. Geolocalización IP (futuro)
    """

    def process_request(self, request):
        # Detectar país desde URL primero
        url_country = self._detect_country_from_url(request)

        # Detectar país desde empresa del usuario (si está autenticado)
        user_country = self._detect_country_from_user(request)

        # NUEVA FUNCIONALIDAD: Verificar conflicto y redirigir si es necesario
        if url_country and user_country and url_country != user_country:
            # Hay conflicto entre URL y empresa - redirigir automáticamente
            return self._handle_country_conflict(request, url_country, user_country)

        # Continuar con la lógica normal si no hay conflicto
        country = url_country

        if not country:
            country = self._detect_country_from_subdomain(request)

        if not country:
            country = user_country

        if not country:
            country = self._detect_country_from_ip(request)

        # Valor por defecto
        if not country:
            country = getattr(settings, "DEFAULT_COUNTRY", "CL")

        request.country = country

        # Debug temporal
        if getattr(settings, "DEBUG", False):
            print(f"CountryContext: {country} (URL: {request.path})")

        return None

    def _handle_country_conflict(self, request, url_country, user_country):
        """
        Maneja conflictos entre país de URL y país de empresa del usuario.
        Redirige automáticamente a la URL correcta del país de la empresa.
        """
        # Construir nueva URL con el país correcto de la empresa
        current_path = request.path

        # Remover prefijo de país actual
        if current_path.startswith(f"/{url_country.lower()}/"):
            new_path = current_path[4:]  # Remover "/us/" o "/cl/"
        elif current_path.startswith(f"/{url_country.lower()}"):
            new_path = current_path[3:]  # Remover "/us" o "/cl"
        else:
            new_path = current_path

        # Agregar prefijo del país correcto
        correct_prefix = f"/{user_country.lower()}"
        if new_path.startswith("/"):
            new_url = f"{correct_prefix}{new_path}"
        else:
            new_url = f"{correct_prefix}/{new_path}"

        # Preservar query string si existe
        if request.GET:
            query_string = request.GET.urlencode()
            new_url = f"{new_url}?{query_string}"

        # Log del conflicto y redirección
        if getattr(settings, "DEBUG", False):
            print(f"🔄 Country Conflict Redirect: {current_path} → {new_url}")
            print(f"   URL Country: {url_country}, User Country: {user_country}")

        # Redirección 302 (temporal) para permitir que el usuario vea el cambio
        return HttpResponseRedirect(new_url)

    def _detect_country_from_url(self, request):
        """Detecta país desde prefijo de URL: /cl/ o /us/ (NUEVOS PREFIJOS)"""
        path = request.path.lower()

        # PRIORIDAD 1: Nuevos prefijos de país (migración completa)
        if re.match(r"^/cl(/|$)", path):
            return "CL"
        elif re.match(r"^/us(/|$)", path):
            return "US"

        # PRIORIDAD 2: Compatibilidad temporal con /es/ = CL, /en/ = US
        # Estos serán redirigidos automáticamente a los nuevos prefijos
        elif re.match(r"^/es(/|$)", path):
            # Marcar para redirección automática a /cl/
            request._needs_country_redirect = ("es", "cl")
            return "CL"
        elif re.match(r"^/en(/|$)", path):
            # Marcar para redirección automática a /us/
            request._needs_country_redirect = ("en", "us")
            return "US"

        return None

    def _detect_country_from_subdomain(self, request):
        """Detecta país desde subdominio: us.domain.com o cl.domain.com"""
        host = request.get_host().lower()

        if host.startswith("us."):
            return "US"
        elif host.startswith("cl."):
            return "CL"

        return None

    def _detect_country_from_user(self, request):
        """Detecta país desde configuración del usuario/empresa"""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        try:
            # Buscar configuración de empresa
            if hasattr(request.user, "empresa") and hasattr(
                request.user.empresa, "pais"
            ):
                return request.user.empresa.pais

            # Buscar configuración de perfil
            if hasattr(request.user, "perfil") and hasattr(request.user.perfil, "pais"):
                return request.user.perfil.pais

        except AttributeError:
            pass

        return None

    def _detect_country_from_ip(self, request):
        """
        Detecta país desde geolocalización de IP (último recurso)
        TODO: Implementar con servicio de geolocalización
        """
        # Por ahora no implementado
        # En el futuro se podría usar GeoIP2 o similar
        return None


class LanguageContextMiddleware(MiddlewareMixin):
    """
    Middleware que detecta idioma preferido del usuario
    Se ejecuta después de CountryContextMiddleware
    """

    def process_request(self, request):
        language = self._detect_language_from_user(request)

        if not language:
            language = self._detect_language_from_url(request)

        if not language:
            # Fallback basado en país
            country = getattr(request, "country", "CL")
            language = "en" if country == "US" else "es"

        request.preferred_language = language

        # Debug temporal
        if getattr(settings, "DEBUG", False):
            print(
                f"🗣️ LanguageContext: {language} (País: {getattr(request, 'country', 'N/A')})"
            )

        return None

    def _detect_language_from_user(self, request):
        """Detecta idioma desde configuración del usuario"""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        try:
            if hasattr(request.user, "perfil") and hasattr(
                request.user.perfil, "idioma_preferido"
            ):
                return request.user.perfil.idioma_preferido
        except AttributeError:
            pass

        return None

    def _detect_language_from_url(self, request):
        """Detecta idioma desde URL (compatibilidad temporal)"""
        path = request.path.lower()

        if re.match(r"^/en(/|$)", path):
            return "en"
        elif re.match(r"^/es(/|$)", path):
            return "es"

        return None
