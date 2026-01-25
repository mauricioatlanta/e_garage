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
        try:
            cfg, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
            data = {
                "COMPANY_ID": empresa.id,
                "COMPANY_NAME": cfg.nombre_publico or getattr(empresa, "nombre", "eGarage"),
                "COMPANY_TAGLINE": cfg.tagline or "",
                "COMPANY_LOGO": getattr(cfg.logo, "url", "") if cfg.logo else "",
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
        except Exception as e:
            # Capturar OperationalError y otros errores de DB (ej: columna 'rubros' no existe)
            # Esto puede ocurrir si faltan migraciones en la base de datos
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error obteniendo ConfiguracionEmpresa en company_header: {e}")
            # Retornar datos mínimos desde la empresa directamente
            data = {
                "COMPANY_ID": empresa.id,
                "COMPANY_NAME": getattr(empresa, "nombre_taller", "eGarage"),
                "COMPANY_TAGLINE": "",
                "COMPANY_LOGO": "",
                "COMPANY_ADDRESS": "",
                "COMPANY_PHONE": getattr(empresa, "telefono", ""),
                "COMPANY_EMAIL": "",
                "COMPANY_WEBSITE": "",
                "COMPANY_CURRENCY": getattr(empresa, "moneda", "CLP"),
                "COMPANY_TAX_RATE": 0,
                "COMPANY_TAX_DEFAULT": False,
                "COMPANY_BRAND_COLOR": "#00E5FF",
            }
            cache.set(cache_key, data, 60)
    return data
