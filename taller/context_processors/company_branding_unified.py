"""
Thin wrapper que expone company_branding() para importaciones legacy.

export_utils y otros módulos importaban directamente desde este archivo.
Ahora delegan a BrandingService para mantener la fuente única de verdad.
"""

from taller.services.branding_service import BrandingService


def company_branding(request):
    """Alias de compatibilidad — delega a BrandingService."""
    brand = BrandingService.get_brand_for_request(request)
    return BrandingService.as_context(brand)
