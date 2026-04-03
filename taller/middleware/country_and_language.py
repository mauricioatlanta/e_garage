from __future__ import annotations

from django.http import HttpResponseRedirect
from django.utils import translation

from taller.utils.country_routing import (
    canonical_lang_for_country,
    canonical_prefix,
    canonicalize_entry_alias,
    default_lang_for_country,
    infer_country,
    infer_language,
    normalize_country,
    parse_country_lang,
)
from taller.utils.empresa import get_user_empresa_safe


EXCLUDED_PREFIXES = (
    "/admin/",
    "/api/",
    "/health/",
    "/health-simple/",
    "/i18n/",
    "/jsi18n/",
    "/static/",
    "/media/",
    "/manifest.json",
    "/service-worker.js",
)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
GLOBAL_CANONICAL_RESTS = {
    "/accounts/login/",
    "/accounts/signup/",
    "/workspace/",
    "/workspace/buscar/",
}


class CountryAndLanguageMiddleware:
    """
    Fuente única para:
    - Canonicalizar `/<pais>/<lang>/...`
    - Resolver aliases legacy (`/login/`, `/workspace/`, `/<pais>/login/`, etc.)
    - Activar idioma final para el request
    - Corregir conflictos entre país de URL y país de empresa autenticada
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        redirect_url = self._get_redirect_url(request)
        if redirect_url:
            return HttpResponseRedirect(redirect_url)

        self._apply_request_locale(request)
        response = self.get_response(request)
        return response

    def _get_redirect_url(self, request) -> str | None:
        path = (request.path or "/").strip() or "/"
        if any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            return None

        path_match = parse_country_lang(path)
        canonical_rest = canonicalize_entry_alias(path_match.rest)
        resolved_country = self._resolved_country(
            request,
            path_match.country,
            canonical_rest if path_match.country else path_match.rest,
        )

        # Compatibilidad para entradas cortas sin resolver por URLConf.
        if path in {"/", ""}:
            return self._with_query(request, f"{canonical_prefix(resolved_country)}/")

        if path_match.country:
            if request.method in MUTATING_METHODS:
                return None
            canonical_lang = self._resolved_lang(request, resolved_country, path_match.lang)
            if path_match.country != resolved_country or path_match.lang != canonical_lang:
                return self._with_query(
                    request,
                    f"{canonical_prefix(resolved_country, canonical_lang)}{canonical_rest}",
                )
            return None

        if request.method in MUTATING_METHODS:
            if canonical_rest == "/accounts/login/":
                canonical_path = (
                    f"{canonical_prefix(resolved_country, self._resolved_lang(request, resolved_country))}"
                    f"{canonical_rest}"
                )
                request.path_info = canonical_path
                request.path = canonical_path
            return None

        if canonical_rest in GLOBAL_CANONICAL_RESTS and (
            canonical_rest != path or path == canonical_rest
        ):
            canonical_lang = self._resolved_lang(request, resolved_country)
            return self._with_query(
                request,
                f"{canonical_prefix(resolved_country, canonical_lang)}{canonical_rest}",
            )

        return None

    def _apply_request_locale(self, request) -> None:
        path_match = parse_country_lang(request.path)
        country = self._resolved_country(request, path_match.country, path_match.rest)
        lang = self._resolved_lang(request, country, path_match.lang)

        request.country = country
        request.country_code = country
        request.LANGUAGE_CODE = lang

        translation.activate(lang)
        try:
            request.session["django_language"] = lang
            request.session["country"] = country.lower()
        except Exception:
            pass

    def _resolved_country(self, request, path_country: str | None, path_rest: str = "/") -> str:
        public_country_scoped_paths = ("/", "/bienvenida/", "/accounts/login/", "/accounts/signup/")
        if path_country and (
            path_rest in {"/"}
            or any(
                path_rest.startswith(public_path) for public_path in public_country_scoped_paths[1:]
            )
        ):
            return path_country

        if getattr(request.user, "is_authenticated", False):
            empresa = getattr(request, "empresa", None) or get_user_empresa_safe(request.user)
            empresa_country = getattr(empresa, "pais", None)
            if empresa_country:
                normalized = normalize_country(empresa_country)
                if normalized:
                    return normalized
        return infer_country(request, fallback=path_country)

    def _resolved_lang(self, request, country: str, path_lang: str | None = None) -> str:
        if path_lang:
            return canonical_lang_for_country(country, path_lang)
        if country == "US":
            return infer_language(request, country, path_lang=path_lang)
        return default_lang_for_country(country)

    def _with_query(self, request, url: str) -> str:
        query = request.META.get("QUERY_STRING", "").strip()
        if query:
            return f"{url}?{query}"
        return url
