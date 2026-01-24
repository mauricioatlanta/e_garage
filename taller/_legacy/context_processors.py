# taller/context_processors.py
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
    }

    if empresa:
        # Usar logo directamente de la empresa si existe
        if hasattr(empresa, "logo") and empresa.logo:
            try:
                brand["logo_url"] = empresa.logo.url
            except Exception:
                pass

        # Usar nombre_taller (no "nombre")
        brand["name"] = getattr(empresa, "nombre_taller", brand["name"]) or brand["name"]

        # Si tiene tagline/lema en la empresa
        if hasattr(empresa, "tagline") and empresa.tagline:
            brand["tagline"] = empresa.tagline
        elif hasattr(empresa, "lema") and empresa.lema:
            brand["tagline"] = empresa.lema

        # País y moneda de la empresa
        brand["country"] = getattr(empresa, "pais", brand["country"]) or brand["country"]
        brand["currency"] = getattr(empresa, "moneda", brand["currency"]) or brand["currency"]

        # Verificar también en ConfiguracionEmpresa si existe
        conf = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()
        if conf:
            if getattr(conf, "logo", None):
                try:
                    brand["logo_url"] = conf.logo.url
                except Exception:
                    pass
            brand["country"] = getattr(conf, "pais", brand["country"]) or brand["country"]
            brand["currency"] = getattr(conf, "moneda", brand["currency"]) or brand["currency"]

    return {"BRAND": brand}
