from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import include, path
from django.utils import translation

from taller.utils.country_routing import allowed_langs_for_country, default_lang_for_country
from taller.views_extra.bienvenida_usa import bienvenida_usa_en, bienvenida_usa_es


def _current_lang_from_path(request: HttpRequest) -> str:
    parts = [part for part in (request.path or "/").strip("/").split("/") if part]
    if parts and parts[0] in {"es", "en", "pt"}:
        return parts[0]
    return "es"


def subdomain_home(request: HttpRequest) -> HttpResponse:
    country = (getattr(request, "country_from_host", None) or "cl").lower()
    lang = _current_lang_from_path(request)

    if lang not in allowed_langs_for_country(country):
        return redirect(f"/{default_lang_for_country(country)}/")

    if country == "us":
        return bienvenida_usa_en(request) if lang == "en" else bienvenida_usa_es(request)

    if country == "br":
        translation.activate("pt")
        request.LANGUAGE_CODE = "pt"
        return render(request, "br/pt/onboarding/bienvenida.html")

    translation.activate("es")
    request.LANGUAGE_CODE = "es"
    return render(request, "cl/es/onboarding/bienvenida.html")


urlpatterns = [
    path("", subdomain_home, name="subdomain_home"),
    path("", include("taller.urls")),
]
