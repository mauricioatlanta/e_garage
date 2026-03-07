"""Paquete de context processors de ``taller``.

Soluciona conflicto entre un archivo ``context_processors.py`` y este
paquete homónimo que impedía que Django resolviera rutas como
``taller.context_processors.empresa_contexto``. Ahora las funciones se
exponen directamente desde el paquete para que ``import_string`` de
Django obtenga el callable correcto.
"""

from django.core.cache import cache

from .company_header import company_header  # ✅ NUEVO - Información de contacto
from .support_context import support_context  # ✅ Información de soporte centralizada

# Traer la función existente definida en submódulo independiente
from .empresa_contexto import empresa_contexto as _empresa_contexto_impl
from .namespaces import ui_namespaces  # útil para otros settings


def company_context(request):
    """Context processor para datos de empresa y configuración estática."""
    try:
        empresa = (
            getattr(request.user, "empresa", None)
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )
        country = getattr(empresa, "pais", "CL") if empresa else "CL"
        company_settings = getattr(empresa, "configuracion", None) if empresa else None
        return {
            "country": country,
            "company_settings": company_settings,
            "STATIC_VERSION": "dev",
            "company": getattr(request, "company", None),
        }
    except Exception as e:
        # Capturar cualquier error (DB, atributos faltantes, etc.)
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Error en company_context: {e}")
        # Retornar valores por defecto seguros
        return {
            "country": "CL",
            "company_settings": None,
            "STATIC_VERSION": "dev",
            "company": None,
        }


def empresa_contexto(request):  # noqa: D401
    """Wrapper que delega en la implementación importada.

    Se define aquí para que el atributo exista en el paquete y Django
    pueda encontrarlo con la ruta acortada utilizada en settings.
    """
    return _empresa_contexto_impl(request)


def _default_brand_dict(settings):
    """Valores por defecto de BRAND para evitar 500 si algo falla."""
    return {
        "logo_url": getattr(settings, "DEFAULT_BRAND_LOGO_URL", None),
        "name": getattr(settings, "DEFAULT_BRAND_NAME", "eGarage"),
        "tagline": getattr(settings, "DEFAULT_BRAND_TAGLINE", "Control total para tu taller"),
        "country": getattr(settings, "DEFAULT_BRAND_COUNTRY", "cl"),
        "currency": getattr(settings, "DEFAULT_BRAND_CURRENCY", "CLP"),
        "primary_color": getattr(settings, "DEFAULT_BRAND_PRIMARY_COLOR", "#0d6efd"),
        "secondary_color": getattr(settings, "DEFAULT_BRAND_SECONDARY_COLOR", "#6c757d"),
    }


def _brand_result(brand):
    """Resultado estándar del context processor a partir del dict brand."""
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


def company_branding(request):
    """
    Context processor unificado de branding.
    Retorna objeto BRAND con todas las propiedades de marca.
    Usa empresa del request (middleware) o del usuario.
    Nunca debe lanzar: ante cualquier error retorna defaults para evitar 500.
    """
    import logging

    from django.conf import settings
    from django.contrib.auth.models import AnonymousUser

    logger = logging.getLogger(__name__)

    try:
        from taller.models import ConfiguracionEmpresa
        from taller.models.company_settings import CompanySettings
        from taller.models.empresa import Empresa
    except Exception as e:
        logger.warning("company_branding: import fallido, usando defaults: %s", e)
        brand = _default_brand_dict(settings)
        return _brand_result(brand)

    user = getattr(request, "user", None)

    # Si estamos en la página raíz o de selección de país, siempre usar "eGarage"
    if request.path == "/" or request.path == "" or "seleccionar_pais" in request.path:
        brand = _default_brand_dict(settings)
        brand["name"] = "eGarage"
        return _brand_result(brand)

    # Defaults del sistema
    brand = _default_brand_dict(settings)

    # Si no hay usuario autenticado, retornar defaults
    if not user or not user.is_authenticated or isinstance(user, AnonymousUser):
        return _brand_result(brand)

    try:
        # Buscar empresa del usuario
        empresa = getattr(request, "empresa_actual", None)
        if not empresa:
            try:
                empresa = Empresa.objects.get(user=user)
            except Empresa.DoesNotExist:
                try:
                    empresa = Empresa.objects.filter(usuario=user).first()
                except Exception:
                    pass

        if empresa:
            # 1. PRIORIDAD MÁXIMA: CompanySettings (tabla nueva)
            try:
                company_settings = CompanySettings.objects.get(user=user)
                if company_settings.logo:
                    brand["logo_url"] = company_settings.logo.url
                if hasattr(company_settings, "company_name") and company_settings.company_name:
                    brand["name"] = company_settings.company_name
                if hasattr(company_settings, "tagline") and company_settings.tagline:
                    brand["tagline"] = company_settings.tagline
                if hasattr(company_settings, "primary_color") and company_settings.primary_color:
                    brand["primary_color"] = company_settings.primary_color
                if (
                    hasattr(company_settings, "secondary_color")
                    and company_settings.secondary_color
                ):
                    brand["secondary_color"] = company_settings.secondary_color
            except CompanySettings.DoesNotExist:
                pass

            # 2. SEGUNDA PRIORIDAD: ConfiguracionEmpresa (si no hay CompanySettings)
            try:
                conf = ConfiguracionEmpresa.objects.get(empresa=empresa)
                if conf.logo and not brand["logo_url"]:
                    brand["logo_url"] = conf.logo.url
                if hasattr(conf, "nombre_publico") and conf.nombre_publico:
                    brand["name"] = conf.nombre_publico
                if hasattr(conf, "tagline") and conf.tagline:
                    brand["tagline"] = conf.tagline
                if hasattr(conf, "brand_color") and conf.brand_color:
                    brand["primary_color"] = conf.brand_color
                if hasattr(conf, "moneda") and conf.moneda:
                    brand["currency"] = conf.moneda
                if hasattr(conf, "pais") and conf.pais:
                    brand["country"] = conf.pais
            except ConfiguracionEmpresa.DoesNotExist:
                pass
            except Exception as e:
                logger.debug("ConfiguracionEmpresa (posible migración faltante): %s", e)

            # 3. TERCERA PRIORIDAD: Empresa directamente (fallback)
            if not brand["logo_url"] and hasattr(empresa, "logo") and empresa.logo:
                brand["logo_url"] = empresa.logo.url
            if brand["name"] == getattr(settings, "DEFAULT_BRAND_NAME", "eGarage"):
                brand["name"] = getattr(empresa, "nombre_taller", brand["name"])
            if hasattr(empresa, "pais") and empresa.pais:
                brand["country"] = (
                    empresa.pais.lower() if isinstance(empresa.pais, str) else empresa.pais
                )
            if hasattr(empresa, "moneda") and empresa.moneda:
                brand["currency"] = empresa.moneda

        return _brand_result(brand)
    except Exception as e:
        logger.warning("company_branding: error inesperado, usando defaults: %s", e)
        return _brand_result(_default_brand_dict(settings))


def company_country(request):
    """
    Inyecta información de país. Prioridad: prefijo URL > request.country > empresa.
    No usar host/dominio: en egarage.cl tanto /us/ como /cl/ existen.
    """
    from taller.utils import get_country_from_request

    return {"company_country": get_country_from_request(request, default="CL")}


def invalidate_company_cache(user):
    """Invalida el caché de branding para un usuario específico.

    Args:
            user: Puede ser un objeto User o un ID de usuario (int)
    """
    if hasattr(user, "id"):
        user_id = user.id
    else:
        user_id = user  # Es un ID directamente

    cache_key = f"company_branding_{user_id}"
    cache.delete(cache_key)


__all__ = [
    "empresa_contexto",
    "company_branding",
    "company_country",
    "company_context",
    "company_header",  # ✅ NUEVO - Información de contacto
    "support_context",  # ✅ Información de soporte centralizada
    "invalidate_company_cache",
    "ui_namespaces",
]
