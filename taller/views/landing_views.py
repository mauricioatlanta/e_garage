from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import render

from commerce.views.catalog import catalog_home
from taller.country.engine import URL_SLUG_TO_VERTICAL, get_hub_landing_urls, get_landing_context
from taller.country.hub import COUNTRY_HUB


def landing_home(request):
    if getattr(request, "is_custom_domain", False):
        return catalog_home(request)
    return render(request, "public/gateway.html")


def render_country_hub(request, country_key):
    ctx = dict(COUNTRY_HUB[country_key])
    ctx["landing_urls"] = get_hub_landing_urls(country_key)
    return render(request, "public/hub_country.html", ctx)


def hub_chile(request):
    return render_country_hub(request, "cl")


def hub_argentina(request):
    return render_country_hub(request, "ar")


def hub_peru(request):
    return render_country_hub(request, "pe")


def hub_mexico(request):
    return render_country_hub(request, "mx")


def hub_ecuador(request):
    return render_country_hub(request, "ec")


def hub_venezuela(request):
    return render_country_hub(request, "ve")


def hub_brasil(request):
    return render_country_hub(request, "br")


def hub_usa_en(request):
    return render_country_hub(request, "us_en")


def hub_usa_es(request):
    return render_country_hub(request, "us_es")


def landing_vertical(request, country_key: str, url_slug: str):
    """
    Unified country-aware landing view.
    URL: /<country_key>/<url_slug>/   e.g. /cl/talleres/ or /ar/gomeria/
    For US: /us/en/<slug>/ and /us/es/<slug>/ are routed here with country_key=us_en/us_es.
    """
    vertical_key = URL_SLUG_TO_VERTICAL.get(url_slug)
    if not vertical_key or country_key not in COUNTRY_HUB:
        raise Http404

    ctx = get_landing_context(country_key, vertical_key)
    return render(request, "public/landing_vertical.html", ctx)


# ── Legacy country-agnostic routes — 301 to Chile equivalents ───────────────

def landing_talleres(request):
    return HttpResponsePermanentRedirect("/cl/talleres/")


def landing_desarmadurias(request):
    return HttpResponsePermanentRedirect("/cl/desarmadurias/")


def landing_repuestos(request):
    return HttpResponsePermanentRedirect("/cl/repuestos/")


def landing_carwash(request):
    return HttpResponsePermanentRedirect("/cl/lavado/")


def landing_vulcanizacion(request):
    return HttpResponsePermanentRedirect("/cl/vulcanizaciones/")


def landing_workshop(request):
    return HttpResponsePermanentRedirect("/cl/talleres/")


def landing_salvage(request):
    return HttpResponsePermanentRedirect("/cl/desarmadurias/")


def landing_parts(request):
    return HttpResponsePermanentRedirect("/cl/repuestos/")
