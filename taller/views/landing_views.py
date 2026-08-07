from django.shortcuts import render

from commerce.views.catalog import catalog_home
from taller.country.hub import COUNTRY_HUB


def landing_home(request):
    if getattr(request, "is_custom_domain", False):
        return catalog_home(request)
    return render(request, "public/gateway.html")


def render_country_hub(request, country):
    ctx = COUNTRY_HUB[country]
    return render(request, "public/hub_country.html", ctx)


def hub_chile(request):
    return render_country_hub(request, "cl")


def hub_argentina(request):
    return render_country_hub(request, "ar")


def hub_peru(request):
    return render_country_hub(request, "pe")


def hub_mexico(request):
    return render_country_hub(request, "mx")


def hub_usa_en(request):
    ctx = COUNTRY_HUB["us"].copy()
    ctx["language"] = "en"
    return render(request, "public/hub_country.html", ctx)


def hub_usa_es(request):
    ctx = COUNTRY_HUB["us"].copy()
    ctx["language"] = "es"
    return render(request, "public/hub_country.html", ctx)


def landing_talleres(request):
    return render(request, "public/landing_talleres.html")


def landing_desarmadurias(request):
    return render(request, "public/landing_desarmadurias.html")


def landing_repuestos(request):
    return render(request, "public/landing_repuestos.html")


def landing_carwash(request):
    return render(request, "public/landing_carwash.html")


def landing_vulcanizacion(request):
    return render(request, "public/landing_vulcanizacion.html")


def landing_workshop(request):
    return render(request, "public/landing_talleres.html")


def landing_salvage(request):
    return render(request, "public/landing_salvage.html")


def landing_parts(request):
    return render(request, "public/landing_repuestos.html")
