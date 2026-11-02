"""Support-only context switcher for superusers.

The selected environment lives in the current session only. It never changes
the superuser's Empresa or ConfiguracionEmpresa records.
"""

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

from taller.utils.country import prefix_from_path
from taller.utils.permisos import normalizar_rubros


SUPPORTED_COUNTRIES = frozenset({"cl", "us", "mx", "ve", "br", "ar", "co", "pe", "ec", "uy"})

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
    import re
    if not request.user.is_superuser:
        return redirect("/")

    if request.method == "POST":
        country = (request.POST.get("country") or request.POST.get("pais") or "cl").lower().strip()
        selected = request.POST.getlist("rubros")

        request.session["support_country"] = country
        request.session["support_rubro"] = selected[0] if selected else ""
        request.session["modo_soporte_rubros"] = selected
        request.session["modo_soporte_pais"] = country
        request.session.modified = True

        referer = request.META.get("HTTP_REFERER", "")
        if country == "us":
            if "/cl/" in referer:
                target = re.sub(r"/cl/(es|en)/", "/us/en/", referer)
                target = re.sub(r"/cl/", "/us/en/", target)
                return redirect(target)
            return redirect("/us/en/desarme/vehiculos/")
        else:
            if "/us/" in referer:
                target = re.sub(r"/us/(en|es)/", f"/{country}/es/", referer)
                target = re.sub(r"/us/", f"/{country}/es/", target)
                return redirect(target)
            return redirect(f"/{country}/es/desarme/vehiculos/")

    return redirect("/")
