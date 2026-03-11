from django.core.cache import cache

from taller.models import ConfiguracionEmpresa
from taller.models.company_settings import CompanySettings
from taller.utils.empresa import get_active_empresa


def invalidate_company_header_cache(empresa_id):
    """Invalida la caché del header para una empresa (llamar al guardar Ajustes)."""
    if empresa_id:
        cache.delete(f"header_conf_{empresa_id}")


def company_header(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}
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
                "COMPANY_NAME": cfg.nombre_publico or getattr(empresa, "nombre_taller", "eGarage"),
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
            # CompanySettings (Ajustes) tiene prioridad para nombre, logo y lema en la cabecera
            try:
                cs = CompanySettings.objects.filter(user=request.user).first()
                if cs:
                    if getattr(cs, "company_name", "").strip():
                        data["COMPANY_NAME"] = cs.company_name.strip()
                    if getattr(cs, "tagline", "").strip():
                        data["COMPANY_TAGLINE"] = cs.tagline.strip()
                    if getattr(cs, "logo", None):
                        try:
                            data["COMPANY_LOGO"] = cs.logo.url
                        except Exception:
                            pass
                    if getattr(cs, "primary_color", "").strip():
                        data["COMPANY_BRAND_COLOR"] = cs.primary_color.strip()
            except Exception:
                pass
            cache.set(cache_key, data, 60)
        except Exception as e:
            # Capturar OperationalError y otros errores de DB (ej: columna 'rubros' no existe)
            import logging

            logger = logging.getLogger(__name__)
            logger.debug("Error obteniendo ConfiguracionEmpresa en company_header: %s", e)
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
            try:
                cs = CompanySettings.objects.filter(user=request.user).first()
                if cs:
                    if getattr(cs, "company_name", "").strip():
                        data["COMPANY_NAME"] = cs.company_name.strip()
                    if getattr(cs, "tagline", "").strip():
                        data["COMPANY_TAGLINE"] = cs.tagline.strip()
                    if getattr(cs, "logo", None):
                        try:
                            data["COMPANY_LOGO"] = cs.logo.url
                        except Exception:
                            pass
            except Exception:
                pass
            cache.set(cache_key, data, 60)
    return data
