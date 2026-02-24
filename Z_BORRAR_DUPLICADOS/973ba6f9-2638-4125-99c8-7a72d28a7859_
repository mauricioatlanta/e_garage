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
        "tagline": getattr(settings, "DEFAULT_BRAND_TAGLINE", "Control total para tu taller"),
        "country": getattr(settings, "DEFAULT_BRAND_COUNTRY", "cl"),
        "currency": getattr(settings, "DEFAULT_BRAND_CURRENCY", "CLP"),
        "primary_color": getattr(settings, "DEFAULT_BRAND_PRIMARY_COLOR", "#0d6efd"),
        "secondary_color": getattr(settings, "DEFAULT_BRAND_SECONDARY_COLOR", "#6c757d"),
    }

    if empresa:
        conf = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()

        # Nombre y datos generales siempre deben reflejar la empresa real,
        # aunque no exista registro en ConfiguracionEmpresa.
        brand["name"] = getattr(empresa, "nombre_taller", brand["name"]) or brand["name"]

        if hasattr(empresa, "pais") and empresa.pais:
            brand["country"] = empresa.pais
        if hasattr(empresa, "moneda") and empresa.moneda:
            brand["currency"] = empresa.moneda

        if conf:
            # Logo
            if getattr(conf, "logo", None):
                try:
                    brand["logo_url"] = conf.logo.url
                except Exception:
                    pass

            # Tagline/lema (si existe)
            if getattr(conf, "lema", None):
                brand["tagline"] = conf.lema
            elif getattr(conf, "tagline", None):
                brand["tagline"] = conf.tagline

            # País y moneda (sobrescriben si están configurados)
            if getattr(conf, "pais", None):
                brand["country"] = conf.pais
            if getattr(conf, "moneda", None):
                brand["currency"] = conf.moneda

            # Colores de marca
            if getattr(conf, "brand_color", None):
                brand["primary_color"] = conf.brand_color
            elif getattr(conf, "color_primario", None):
                brand["primary_color"] = conf.color_primario

            if getattr(conf, "color_secundario", None):
                brand["secondary_color"] = conf.color_secundario
        else:
            # Sin configuración explícita, intentar usar lema del modelo Empresa
            if getattr(empresa, "lema", None):
                brand["tagline"] = empresa.lema

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
