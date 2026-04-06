from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .core.locale_router import resolve_country_lang


COOKIE_COUNTRY = "eg_country"
COOKIE_LANG = "eg_lang"
COOKIE_MAX_AGE = 60 * 60 * 24 * 180


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
        "suggested_url": decision.target_url,
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

    response = redirect(decision.target_url)
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

    response = redirect(decision.target_url)
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
