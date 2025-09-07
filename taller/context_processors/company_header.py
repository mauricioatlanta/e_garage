from django.core.cache import cache

from taller.models import ConfiguracionEmpresa
from taller.utils.empresa import get_active_empresa


def company_header(request):
    empresa = get_active_empresa(request)
    if not empresa:
        return {}

    cache_key = f"header_conf_{empresa.id}"
    data = cache.get(cache_key)
    if not data:
        cfg, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
        data = {
            "COMPANY_ID": empresa.id,
            "COMPANY_NAME": cfg.nombre_publico or getattr(empresa, "nombre", "eGarage"),
            "COMPANY_TAGLINE": cfg.tagline or "",
            "COMPANY_LOGO": getattr(cfg.logo, "url", ""),
            "COMPANY_ADDRESS": cfg.direccion or "",
            "COMPANY_PHONE": cfg.telefono or "",
            "COMPANY_EMAIL": cfg.email_contacto or "",
            "COMPANY_WEBSITE": cfg.sitio_web or "",
            "COMPANY_CURRENCY": cfg.moneda,
            "COMPANY_TAX_RATE": cfg.tasa_impuesto,
            "COMPANY_TAX_DEFAULT": cfg.aplicar_impuesto_por_defecto,
            "COMPANY_BRAND_COLOR": getattr(cfg, "brand_color", "#00E5FF"),
        }
        cache.set(cache_key, data, 60)
    return data
