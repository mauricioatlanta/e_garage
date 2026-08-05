from django.shortcuts import render

from commerce.views.catalog import catalog_home


def landing_home(request):
    if getattr(request, "is_custom_domain", False):
        return catalog_home(request)

    return render(request, "public/home.html")


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


# Aliases en inglés (backward compat)
def landing_workshop(request):
    return render(request, "public/landing_talleres.html")


def landing_salvage(request):
    return render(request, "public/landing_salvage.html")


def landing_parts(request):
    return render(request, "public/landing_repuestos.html")
