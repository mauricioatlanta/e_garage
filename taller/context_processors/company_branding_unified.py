# taller/context_processors/company_branding_unified.py

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from taller.models import ConfiguracionEmpresa  # ajusta import si cambia el path


def company_branding(request):
    """
    Entrega always-on branding:
    BRAND.logo_url, BRAND.name, BRAND.tagline, BRAND.country, BRAND.currency
    Usa la empresa del request (middleware/tenant) o, si no, la del usuario.
    """
    empresa = getattr(request, "empresa_actual", None)

    # Fallbacks: si tu middleware no setea empresa_actual, intenta por usuario
    if (
        not empresa
        and getattr(request, "user", None)
        and not isinstance(request.user, AnonymousUser)
    ):
        # Intentar múltiples formas de obtener la empresa
        empresa = getattr(getattr(request.user, "perfil", None), "empresa", None) or getattr(
            request.user, "empresa", None
        )

    brand = {
        "logo_url": getattr(
            settings, "DEFAULT_BRAND_LOGO_URL", "/static/branding/egarage_logo.svg"
        ),
        "name": getattr(settings, "DEFAULT_BRAND_NAME", "eGarage"),
        "tagline": getattr(settings, "DEFAULT_BRAND_TAGLINE", "Mission Control for your Workshop"),
        "country": getattr(settings, "DEFAULT_BRAND_COUNTRY", "cl"),
        "currency": getattr(settings, "DEFAULT_BRAND_CURRENCY", "CLP"),
        "primary_color": getattr(settings, "DEFAULT_BRAND_PRIMARY_COLOR", "#0d6efd"),
        "secondary_color": getattr(settings, "DEFAULT_BRAND_SECONDARY_COLOR", "#6c757d"),
    }

    if empresa:
        conf = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()
        if conf:
            # Logo
            if getattr(conf, "logo", None):
                try:
                    brand["logo_url"] = conf.logo.url
                except Exception:
                    pass

            # Nombre de la empresa
            brand["name"] = getattr(empresa, "nombre_taller", brand["name"]) or brand["name"]

            # Tagline/lema (si existe en ConfiguracionEmpresa)
            if hasattr(conf, "lema") and conf.lema:
                brand["tagline"] = conf.lema
            elif hasattr(conf, "tagline") and conf.tagline:
                brand["tagline"] = conf.tagline

            # País y moneda
            if hasattr(conf, "pais"):
                brand["country"] = getattr(conf, "pais", brand["country"]) or brand["country"]
            elif hasattr(empresa, "pais"):
                brand["country"] = getattr(empresa, "pais", brand["country"]) or brand["country"]

            if hasattr(conf, "moneda"):
                brand["currency"] = getattr(conf, "moneda", brand["currency"]) or brand["currency"]
            elif hasattr(empresa, "moneda"):
                brand["currency"] = (
                    getattr(empresa, "moneda", brand["currency"]) or brand["currency"]
                )

            # Colores de marca
            if hasattr(conf, "brand_color") and conf.brand_color:
                brand["primary_color"] = conf.brand_color
            elif hasattr(conf, "color_primario") and conf.color_primario:
                brand["primary_color"] = conf.color_primario

            if hasattr(conf, "color_secundario") and conf.color_secundario:
                brand["secondary_color"] = conf.color_secundario

    # Backwards compatibility: también exponer las variables individuales
    return {
        "BRAND": brand,
        # Compatibility con código existente
        "company_name": brand["name"],
        "company_logo_url": brand["logo_url"],
        "company_tagline": brand.get("tagline"),
        "primary_color": brand["primary_color"],
        "secondary_color": brand["secondary_color"],
        "company_color": brand["primary_color"],
        "company_country": brand["country"],
        "company_currency": brand["currency"],
    }
