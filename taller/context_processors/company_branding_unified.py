from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from taller.models import ConfiguracionEmpresa


def company_branding(request):
    empresa = getattr(request, "empresa", None)

    if (
        not empresa
        and getattr(request, "user", None)
        and not isinstance(request.user, AnonymousUser)
    ):
        try:
            empresa = request.user.empresa
        except Exception:
            empresa = None

    brand = {
        "logo_url": getattr(
            settings, "DEFAULT_BRAND_LOGO_URL", "/static/img/logo.png"
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

        brand["name"] = getattr(empresa, "nombre_taller", brand["name"]) or brand["name"]

        if getattr(empresa, "pais", None):
            brand["country"] = empresa.pais
        if getattr(empresa, "moneda", None):
            brand["currency"] = empresa.moneda

        if conf:
            if getattr(conf, "logo", None):
                try:
                    brand["logo_url"] = conf.logo.url
                except Exception:
                    pass

            if getattr(conf, "lema", None):
                brand["tagline"] = conf.lema

    return {
        "BRAND": brand,
        "company_name": brand["name"],
        "company_logo_url": brand["logo_url"],
        "company_tagline": brand.get("tagline"),
        "primary_color": brand["primary_color"],
        "secondary_color": brand["secondary_color"],
        "company_color": brand["primary_color"],
        "company_country": brand["country"],
        "company_currency": brand["currency"],
    }
