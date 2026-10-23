"""Support-only context switcher for superusers.

The selected environment lives in the current session only. It never changes
the superuser's Empresa or ConfiguracionEmpresa records.
"""

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect


SUPPORTED_COUNTRIES = frozenset({"cl", "us", "mx", "ve", "br", "ar", "co", "pe", "ec", "uy"})

SUPPORTED_RUBROS = {
    "TALLER": "WORKSHOP",
    "DESARME": "DESARMADURIA",
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
        else:
            country = (request.POST.get("country") or "").strip().lower()
            rubro = (request.POST.get("rubro") or "").strip().upper()
            if country in SUPPORTED_COUNTRIES and rubro in SUPPORTED_RUBROS:
                request.session["support_country"] = country
                request.session["support_rubro"] = SUPPORTED_RUBROS[rubro]

    return redirect(request.META.get("HTTP_REFERER", "/"))
