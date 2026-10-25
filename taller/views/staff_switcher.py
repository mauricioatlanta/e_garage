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

    return redirect(request.META.get("HTTP_REFERER", "/"))
