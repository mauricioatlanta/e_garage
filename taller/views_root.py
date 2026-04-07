from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .core.locale_router import resolve_country_lang
from .utils.country_routing import default_lang_for_country
from .utils.url_strategy import build_country_lang_path
from .views_root_country import country_lang_root_view


COOKIE_COUNTRY = "eg_country"
COOKIE_LANG = "eg_lang"
COOKIE_MAX_AGE = 60 * 60 * 24 * 180


def _localized_target_url(request: HttpRequest, country: str, lang: str) -> str:
    return build_country_lang_path(request, country, lang, "/")


def redirect_to_home(request: HttpRequest) -> HttpResponse:
    country = (getattr(request, "country_from_host", None) or "").upper()

    if not country and request.user.is_authenticated:
        try:
            if hasattr(request.user, "empresa") and request.user.empresa:
                country = (request.user.empresa.pais or "").upper()
        except Exception:
            pass

    if not country:
        country = (getattr(request, "country", None) or "CL").upper()

    lang = default_lang_for_country(country)
    return redirect(build_country_lang_path(request, country, lang, "/"))


def root_landing(request: HttpRequest) -> HttpResponse:
    decision = resolve_country_lang(
        cookie_country=request.COOKIES.get(COOKIE_COUNTRY),
        cookie_lang=request.COOKIES.get(COOKIE_LANG),
        cf_country=request.headers.get("cf-ipcountry"),
        accept_language=request.headers.get("accept-language"),
    )

    context = {
        "suggested_country": decision.country,
        "suggested_lang": decision.lang,
        "suggested_url": _localized_target_url(request, decision.country, decision.lang),
        "decision_source": decision.source,
    }
    return render(request, "public/root_landing.html", context)


def root_autoredirect(request: HttpRequest) -> HttpResponse:
    decision = resolve_country_lang(
        cookie_country=request.COOKIES.get(COOKIE_COUNTRY),
        cookie_lang=request.COOKIES.get(COOKIE_LANG),
        cf_country=request.headers.get("cf-ipcountry"),
        accept_language=request.headers.get("accept-language"),
    )

    response = redirect(_localized_target_url(request, decision.country, decision.lang))
    response.set_cookie(
        COOKIE_COUNTRY,
        decision.country,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
        secure=True,
    )
    response.set_cookie(
        COOKIE_LANG,
        decision.lang,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
        secure=True,
    )
    return response


def select_region(request: HttpRequest, country: str, lang: str) -> HttpResponse:
    decision = resolve_country_lang(
        cookie_country=(country or "").upper(),
        cookie_lang=(lang or "").lower(),
        cf_country=None,
        accept_language=None,
    )

    response = redirect(_localized_target_url(request, decision.country, decision.lang))
    response.set_cookie(
        COOKIE_COUNTRY,
        decision.country,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
        secure=True,
    )
    response.set_cookie(
        COOKIE_LANG,
        decision.lang,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
        secure=True,
    )
    return response


def workspace_router_view(request: HttpRequest) -> HttpResponse:
    return country_lang_root_view(request)
