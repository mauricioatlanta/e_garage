"""Support-only context switcher for superusers.

The selected environment lives in the current session only. It never changes
the superuser's Empresa or ConfiguracionEmpresa records.
"""

from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.utils import translation

from taller.utils.country import prefix_from_path
from taller.utils.permisos import normalizar_rubros


SUPPORTED_COUNTRIES = frozenset({"cl", "us", "mx", "ve", "br", "ar", "co", "pe", "ec", "uy"})

# Segmentos de idioma reconocidos en el prefijo de URL (/us/en/, /cl/es/, /br/pt/).
_URL_LANG_SEGMENTS = frozenset({"en", "es", "pt"})


def _set_language_cookie(response, lang):
    """Persiste la preferencia de idioma en la cookie django_language."""
    response.set_cookie(
        getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language"),
        lang,
        max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", 60 * 60 * 24 * 365),
        path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
        domain=getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None),
        secure=getattr(settings, "LANGUAGE_COOKIE_SECURE", False),
        httponly=getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False),
        samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", "Lax"),
    )


def _rewrite_to_us_en(referer):
    """Reescribe el path de *referer* al equivalente /us/en/<resto>/."""
    parsed = urlparse(referer)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if parts and parts[0].lower() in SUPPORTED_COUNTRIES:
        parts = parts[1:]
        if parts and parts[0].lower() in _URL_LANG_SEGMENTS:
            parts = parts[1:]
    rest = "/".join(parts)
    new_path = "/us/en"
    if rest:
        new_path = f"/us/en/{rest}/"
    return urlunparse(
        (parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment)
    )


SUPPORTED_RUBROS = {
    "TALLER": "WORKSHOP",
    "DESARME": "DESARMADURIA",
    "REPUESTOS": "PARTS",
    "VULCANIZACION": "TIRE",
    "CARWASH": "DETAILING",
    "GRUAS": "TOWING",
}

SUPPORTED_RUBROS_MULTI = {
    "TALLER": "WORKSHOP",
    "DESARMADURIA": "DESARMADURIA",
    "REPUESTOS": "PARTS",
    "VULCANIZACION": "TIRE",
    "CARWASH": "DETAILING",
    "GRUAS": "TOWING",
}


@user_passes_test(lambda user: user.is_superuser)
def switch_support_environment(request):
    """Set or reset the support country and business context for this session."""
    if request.method == "POST":
        if request.POST.get("action") == "reset":
            request.session.pop("support_country", None)
            request.session.pop("support_rubro", None)
            request.session.pop("modo_soporte_rubros", None)
        else:
            country = (request.POST.get("country") or "").strip().lower()
            rubro = (request.POST.get("rubro") or "").strip().upper()
            selected = request.POST.getlist("rubros")
            selected = [SUPPORTED_RUBROS_MULTI.get(str(value).strip().upper(), "") for value in selected]
            selected = normalizar_rubros([value for value in selected if value])
            if not selected and rubro in SUPPORTED_RUBROS:
                selected = [SUPPORTED_RUBROS[rubro]]

            if country in SUPPORTED_COUNTRIES and selected:
                request.session["support_country"] = country
                request.session["support_rubro"] = selected[0]
                request.session["modo_soporte_rubros"] = selected

                # Switching to Grúas must open its operational board. Keeping
                # the previous URL (for example /documentos/) leaves the
                # towing navigation active over a workshop-oriented screen.
                if selected[0] == "TOWING":
                    prefix = prefix_from_path(request.path) or f"{country}/es"
                    return redirect(f"/{prefix}/gruas/")

                # USA → inglés: activar en, persistir cookie+session y redirigir
                # a /us/en/... para que las vistas carguen los templates us/en.
                if country == "us":
                    request.session["django_language"] = "en"
                    request.session["preferred_lang"] = "en"
                    request.session.modified = True
                    translation.activate("en")
                    request.LANGUAGE_CODE = "en"

                    referer = request.META.get("HTTP_REFERER", "")
                    target = _rewrite_to_us_en(referer) if referer else "/us/en/"
                    response = redirect(target)
                    _set_language_cookie(response, "en")
                    return response

    return redirect(request.META.get("HTTP_REFERER", "/"))
