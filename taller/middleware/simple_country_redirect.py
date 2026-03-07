"""
Middleware: una sola fuente de verdad = prefijo de URL.
Si el usuario tiene empresa y la URL está bajo un prefijo de país activo
(settings.EGARAGE_ACTIVE_COUNTRIES), el país de la URL debe coincidir con
empresa.pais. Si no coincide, redirige a la URL correcta del país de la
empresa (mismo path, otro prefijo). Idioma por país viene de
settings.EGARAGE_COUNTRY_DEFAULT_LANG.
"""

import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

log = logging.getLogger(__name__)

# Idiomas reconocidos en el path (es, en)
_SUPPORTED_LANGS = ("es", "en")


def _path_after_country_lang(path, url_country_lower):
    """Extrae el path tras el prefijo /<country>/ o /<country>/<lang>/."""
    path = (path or "").strip().rstrip("/") or "/"
    parts = [p for p in path.split("/") if p]
    if not parts:
        return ""
    if parts[0].lower() != url_country_lower:
        return path.lstrip("/")
    if len(parts) >= 2 and parts[1].lower() in _SUPPORTED_LANGS:
        rest = parts[2:]
    else:
        rest = parts[1:]
    return "/" + "/".join(rest) if rest else ""


def _get_active_countries():
    """Países con prefijo de URL; por defecto CL, US. Escalar vía settings.EGARAGE_ACTIVE_COUNTRIES."""
    return getattr(settings, "EGARAGE_ACTIVE_COUNTRIES", ("CL", "US"))


def _get_country_default_lang():
    """Mapeo país → idioma por defecto. Por defecto US→en, CL→es; resto→es."""
    return getattr(settings, "EGARAGE_COUNTRY_DEFAULT_LANG", {"US": "en", "CL": "es"})


class SimpleCountryRedirectMiddleware(MiddlewareMixin):
    """
    Fuente de verdad = prefijo de URL. La empresa activa debe coincidir con ese país.
    Si no coincide: redirige a la URL correcta del país de la empresa.
    Usa settings.EGARAGE_ACTIVE_COUNTRIES y EGARAGE_COUNTRY_DEFAULT_LANG (escalable LATAM).
    """

    def process_request(self, request):
        # No redirigir mutaciones (evita perder body POST, convertir a GET, romper CSRF)
        if request.method not in ("GET", "HEAD"):
            return None

        if not getattr(request.user, "is_authenticated", False):
            return None

        # 0) Preferir empresa activa en sesión
        empresa = None
        empresa_id = request.session.get("empresa_id")
        if empresa_id:
            try:
                from taller.models import Empresa

                empresa = Empresa.objects.filter(id=empresa_id).only("id", "pais").first()
            except Exception:
                empresa = None

        # 1) Fallbacks
        if not empresa:
            empresa = getattr(request, "empresa", None) or getattr(
                getattr(request, "user", None), "empresa", None
            )

        if not empresa:
            return None

        user_country = (getattr(empresa, "pais", None) or "").strip().upper()
        active = _get_active_countries()
        if not user_country or user_country not in active:
            return None

        path_lower = (request.path or "").lower()
        url_country = None
        url_lang = None
        for country in active:
            if path_lower.startswith(f"/{country.lower()}/"):
                url_country = country
                for lang in _SUPPORTED_LANGS:
                    if path_lower.startswith(f"/{country.lower()}/{lang}/"):
                        url_lang = lang
                        break
                break

        if not url_country:
            return None

        country_lang = _get_country_default_lang()
        correct_lang = country_lang.get(user_country, "es")
        rest = _path_after_country_lang(request.path, url_country.lower())

        # Never redirect login/signup paths: /us/login/, /us/accounts/login/, etc.
        # Redirecting to /us/en/login/ can 404 or cause ERR_TOO_MANY_REDIRECTS.
        rest_lower = (rest or "").lower()
        if (
            "/login" in rest_lower
            or "/accounts/login" in rest_lower
            or "/signup" in rest_lower
            or "/accounts/signup" in rest_lower
        ):
            return None

        if url_country != user_country:
            new_url = f"/{user_country.lower()}/{correct_lang}/{rest.lstrip('/')}"
            qs = request.META.get("QUERY_STRING", "").strip()
            if qs:
                new_url += "?" + qs
            log.debug(
                "Country mismatch: redirect %s -> %s (empresa=%s)",
                request.path,
                new_url,
                user_country,
            )
            return HttpResponseRedirect(new_url)

        # Corrige también cuando NO hay idioma en URL (ej. /cl/vehiculos/crear/ -> /cl/es/vehiculos/crear/)
        if (url_lang or "") != correct_lang:
            new_url = f"/{user_country.lower()}/{correct_lang}/{rest.lstrip('/')}"
            qs = request.META.get("QUERY_STRING", "").strip()
            if qs:
                new_url += "?" + qs
            log.debug("Lang mismatch: redirect %s -> %s", request.path, new_url)
            return HttpResponseRedirect(new_url)

        return None
