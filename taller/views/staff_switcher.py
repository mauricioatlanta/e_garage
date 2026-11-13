from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

# Mapa slug del formulario -> valor REAL de ConfiguracionEmpresa.rubro_principal / RUBRO_TO_PRODUCT
# OJO: en product_profiles.py PRODUCT_TIRE = "TIRE", PRODUCT_DESARMADURIA = "DESARMADURIA"
# NO usar "PRODUCT_TIRE" ni "PRODUCT_DESARME", esos no existen.
RUBRO_MAP = {
    "taller": "WORKSHOP",
    "taller_mecanico": "WORKSHOP",
    "mecanico": "WORKSHOP",
    "workshop": "WORKSHOP",
    "desarmaduria": "DESARMADURIA",
    "desarme": "DESARMADURIA",
    "casa_de_repuestos": "PARTS",
    "repuestos": "PARTS",
    "parts": "PARTS",
    "vulcanizacion": "TIRE",
    "vulcanización": "TIRE",
    "tire": "TIRE",
    "product_tire": "TIRE",
    "carwash": "DETAILING",
    "detailing": "DETAILING",
    "gruas": "TOWING",
    "gruas_y_asistencia_vial": "TOWING",
    "towing": "TOWING",
    "reciclaje": "RECYCLING",
    "recycling": "RECYCLING",
}
TARGET_MAP = {
    "DESARMADURIA": "/{country}/{lang}/desarme/vehiculos/",
    "TIRE": "/{country}/{lang}/workspace/",
    "WORKSHOP": "/{country}/{lang}/workspace/",
    "PARTS": "/{country}/{lang}/workspace/",
    "DETAILING": "/{country}/{lang}/workspace/",
    "TOWING": "/{country}/{lang}/workspace/",
    "RECYCLING": "/{country}/{lang}/workspace/",
}

@csrf_exempt
def switch_support_environment(request):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect("/cl/es/accounts/login/")
    if request.method == "POST":
        country = (request.POST.get("country") or request.POST.get("pais") or "cl").lower().strip()
        selected_raw = request.POST.getlist("rubros")
        if not selected_raw:
            single = request.POST.get("rubro") or request.POST.get("rubros")
            if single:
                selected_raw = [single]
        selected_slugs = []
        for r in selected_raw:
            s = str(r).strip().lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
            selected_slugs.append(s)
        # Primer rubro = rubro_principal real
        rubro_principal = "WORKSHOP"
        if selected_slugs:
            rubro_principal = RUBRO_MAP.get(selected_slugs[0], selected_slugs[0].upper())
        # Guardar en los 3 formatos que usan los distintos archivos del proyecto
        rubros_principales = [RUBRO_MAP.get(s, s.upper()) for s in selected_slugs] or [rubro_principal]
        request.session["support_country"] = country
        request.session["modo_soporte_pais"] = country
        request.session["support_rubro"] = rubro_principal
        request.session["support_rubros"] = rubros_principales
        request.session["modo_soporte_rubros"] = selected_slugs
        request.session["modo_soporte_rubro_principal"] = rubro_principal
        request.session["modo_soporte_activo"] = True
        lang = "en" if country == "us" else ("pt" if country == "br" else "es")
        request.session["django_language"] = lang
        request.session.modified = True
        target_tpl = TARGET_MAP.get(rubro_principal, "/{country}/{lang}/workspace/")
        target = target_tpl.format(country=country, lang=lang)
        response = redirect(target)
        response.set_cookie("django_language", lang, max_age=365*24*60*60, path="/")
        return response
    country = request.session.get("support_country") or "cl"
    return redirect(f"/{country}/{lang}/workspace/")
