"""
Middleware para redirecciones automáticas de URLs legacy
Migra /es/ → /cl/ y /en/ → /us/ con redirecciones 301
"""

import re

from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class CountryURLRedirectMiddleware(MiddlewareMixin):
    """
    Middleware que maneja redirecciones 301 desde URLs legacy
    Debe ejecutarse ANTES de CountryContextMiddleware
    """

    URL_MIGRATIONS = {
        "es": "cl",  # /es/ → /cl/
        "en": "us",  # /en/ → /us/
    }

    def process_request(self, request):
        """Procesa request y redirige URLs legacy si es necesario"""
        path = request.path.lower()

        # Verificar si la URL necesita redirección
        for old_prefix, new_prefix in self.URL_MIGRATIONS.items():
            pattern = f"^/{old_prefix}(/|$)"
            if re.match(pattern, path):
                # Construir nueva URL
                new_path = re.sub(f"^/{old_prefix}", f"/{new_prefix}", request.path)

                # Preservar query string si existe
                if request.GET:
                    query_string = request.GET.urlencode()
                    new_url = f"{new_path}?{query_string}"
                else:
                    new_url = new_path

                # Log de migración (temporal para debugging)
                if hasattr(request, "user") and request.user.is_authenticated:
                    print(
                        f"🔄 URL Migration: {request.path} → {new_url} (User: {request.user.username})"
                    )
                else:
                    print(f"🔄 URL Migration: {request.path} → {new_url} (Anonymous)")

                # Redirección 301 (permanente)
                return HttpResponsePermanentRedirect(new_url)

        return None

    def process_response(self, request, response):
        """Procesa response para agregar headers de migración si es necesario"""
        # Agregar header informativo sobre la migración
        if hasattr(request, "_needs_country_redirect"):
            old_prefix, new_prefix = request._needs_country_redirect
            response["X-URL-Migration"] = f"{old_prefix}-to-{new_prefix}"
            response["X-Migration-Info"] = (
                "Legacy URL prefix detected, please update to new country-based URLs"
            )

        return response


class CountryURLPatternHelper:
    """
    Helper class para generar URLs correctas con prefijos de país
    """

    COUNTRY_PREFIXES = {
        "CL": "cl",
        "US": "us",
        # Futuros países
        "MX": "mx",
        "CO": "co",
        "AR": "ar",
    }

    @classmethod
    def get_url_prefix(cls, country):
        """Obtiene prefijo de URL para un país"""
        return cls.COUNTRY_PREFIXES.get(country, "cl")  # Default CL

    @classmethod
    def build_country_url(cls, country, path=""):
        """Construye URL completa con prefijo de país"""
        prefix = cls.get_url_prefix(country)
        if not path.startswith("/"):
            path = "/" + path
        return f"/{prefix}{path}"

    @classmethod
    def extract_country_from_url(cls, url):
        """Extrae código de país desde URL"""
        for country, prefix in cls.COUNTRY_PREFIXES.items():
            if url.startswith(f"/{prefix}/") or url == f"/{prefix}":
                return country
        return None

    @classmethod
    def get_available_countries(cls):
        """Obtiene lista de países disponibles"""
        return list(cls.COUNTRY_PREFIXES.keys())

    @classmethod
    def get_country_switch_urls(cls, current_url, target_countries=None):
        """
        Genera URLs para cambiar de país manteniendo la misma página

        Args:
            current_url: URL actual (ej: /cl/clientes/)
            target_countries: Lista de países objetivo (default: todos)

        Returns:
            Dict con URLs por país
        """
        if target_countries is None:
            target_countries = cls.get_available_countries()

        # Extraer path sin prefijo de país
        path_without_prefix = current_url
        for country, prefix in cls.COUNTRY_PREFIXES.items():
            if current_url.startswith(f"/{prefix}/"):
                path_without_prefix = current_url[len(f"/{prefix}") :]
                break
            elif current_url == f"/{prefix}":
                path_without_prefix = "/"
                break

        # Generar URLs para cada país
        switch_urls = {}
        for country in target_countries:
            switch_urls[country] = cls.build_country_url(country, path_without_prefix)

        return switch_urls


# Funciones de conveniencia para templates y views
def get_country_url(country, path=""):
    """Función de conveniencia para obtener URL de país"""
    return CountryURLPatternHelper.build_country_url(country, path)


def get_current_country_from_request(request):
    """Función de conveniencia para obtener país actual desde request"""
    return getattr(request, "country", "CL")


def get_country_switch_urls_for_request(request):
    """Función de conveniencia para obtener URLs de cambio de país"""
    return CountryURLPatternHelper.get_country_switch_urls(request.path)
