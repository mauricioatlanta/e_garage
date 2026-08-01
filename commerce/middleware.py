"""
CommerceTenantMiddleware

Corre después de HostTenantMiddleware. Fuente de verdad del tenant Commerce:
  1. request.empresa  — resuelto por HostTenantMiddleware desde EmpresaDominio.
  2. COMMERCE_TENANT_MAP — fallback para entornos de desarrollo / migración.

Siempre setea request.commerce_empresa (alias para compatibilidad con código
legado) y request.commerce_brand.

Una vez que todos los tenants tengan un EmpresaDominio activo, este middleware
puede eliminarse: basta con que las vistas lean request.empresa directamente.
"""
from django.conf import settings


class CommerceTenantMiddleware:

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        empresa = getattr(request, "empresa", None) or self._resolve_from_map(request)
        request.commerce_empresa = empresa  # alias de compatibilidad
        if empresa is not None:
            from commerce.services.storefront_service import CommerceStorefrontService
            request.commerce_brand = CommerceStorefrontService.resolve(empresa)
        else:
            request.commerce_brand = None
        return self._get_response(request)

    @staticmethod
    def _resolve_from_map(request):
        tenant_map = getattr(settings, "COMMERCE_TENANT_MAP", {})
        if not tenant_map:
            return None
        host = request.get_host().split(":")[0]
        empresa_id = tenant_map.get(host)
        if not empresa_id:
            return None
        from taller.models import Empresa
        return Empresa.objects.filter(pk=empresa_id).first()
