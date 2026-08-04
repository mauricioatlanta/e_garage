"""Paquete de context processors de ``taller``.

Soluciona conflicto entre un archivo ``context_processors.py`` y este
paquete homónimo que impedía que Django resolviera rutas como
``taller.context_processors.empresa_contexto``. Ahora las funciones se
exponen directamente desde el paquete para que ``import_string`` de
Django obtenga el callable correcto.
"""

from django.core.cache import cache

from .business_modules import business_modules  # módulos de negocio dinámicos
from .company_header import company_header  # ✅ NUEVO - Información de contacto
from .support_context import support_context  # ✅ Información de soporte centralizada

# Traer la función existente definida en submódulo independiente
from .empresa_contexto import empresa_contexto as _empresa_contexto_impl
from .namespaces import ui_namespaces  # útil para otros settings


def company_context(request):
    """Context processor para datos de empresa y configuración estática."""
    empresa = None
    if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
        try:
            from taller.utils.empresa import get_user_empresa_safe

            empresa = get_user_empresa_safe(request.user)
        except Exception:
            empresa = None
    country = getattr(empresa, "pais", "CL") if empresa else "CL"
    company_settings = getattr(empresa, "configuracion", None) if empresa else None
    return {
        "country": country,
        "company_settings": company_settings,
        "STATIC_VERSION": "dev",
        "company": getattr(request, "company", None),
    }


def empresa_contexto(request):  # noqa: D401
    """Wrapper que delega en la implementación importada.

    Se define aquí para que el atributo exista en el paquete y Django
    pueda encontrarlo con la ruta acortada utilizada en settings.
    """
    return _empresa_contexto_impl(request)


def _first_nonempty(*values):
    for value in values:
        if value:
            value = str(value).strip()
            if value:
                return value
    return ""


def company_branding(request):
    """
    Context processor de branding — delega a BrandingService.

    URLs de la landing (/ o seleccionar_pais) siempre devuelven la marca
    de la plataforma (eGarage) independientemente del usuario autenticado.
    """
    from taller.services.branding_service import BrandingService

    if request.path in ("/", "") or "seleccionar_pais" in request.path:
        brand = BrandingService._defaults()
        brand.name = "eGarage"
        return BrandingService.as_context(brand)

    from django.contrib.auth.models import AnonymousUser

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or isinstance(user, AnonymousUser):
        return BrandingService.as_context(BrandingService._defaults())

    brand = BrandingService.get_brand_for_request(request)
    return BrandingService.as_context(brand)


def company_country(request):
    """Inyecta información de país de la empresa."""
    from taller.models.empresa import Empresa

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"company_country": "CL"}

    try:
        empresa = Empresa.objects.get(user=user)
        return {"company_country": empresa.pais}
    except Empresa.DoesNotExist:
        return {"company_country": "CL"}


def invalidate_company_cache(user):
    """Invalida el caché de company_header para un usuario específico."""
    user_id = user.id if hasattr(user, "id") else user
    try:
        from taller.models.empresa import Empresa
        empresa = Empresa.objects.get(user_id=user_id)
        cache.delete(f"header_conf_{empresa.id}")
    except Exception:
        pass


__all__ = [
    "business_modules",
    "empresa_contexto",
    "company_branding",
    "company_country",
    "company_context",
    "company_header",  # ✅ NUEVO - Información de contacto
    "support_context",  # ✅ Información de soporte centralizada
    "invalidate_company_cache",
    "ui_namespaces",
]
