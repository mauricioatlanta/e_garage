"""
CommerceTenantMiddleware

Resuelve el tenant Commerce (Empresa) a partir del hostname del request.
Setea request.commerce_empresa y request.commerce_brand en cada petición.

Configuración en settings (ejemplo):
    COMMERCE_TENANT_MAP = {
        "monteazul.local": 2,   # empresa_id
        "monteazul.cl": 2,
    }

En producción, Nginx puede rutear monteazul.cl al mismo Django.
El middleware resuelve el tenant y Commerce sirve el catálogo correcto.

commerce_brand solo se resuelve cuando existe un tenant activo, de modo
que las URLs del ERP (donde COMMERCE_TENANT_MAP no coincide) no pagan
el costo de las consultas adicionales.
"""
from django.conf import settings


class CommerceTenantMiddleware:

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        empresa = self._resolve_tenant(request)
        request.commerce_empresa = empresa
        if empresa is not None:
            from commerce.services.storefront_service import CommerceStorefrontService
            request.commerce_brand = CommerceStorefrontService.resolve(empresa)
        else:
            request.commerce_brand = None
        return self._get_response(request)

    @staticmethod
    def _resolve_tenant(request):
        tenant_map = getattr(settings, "COMMERCE_TENANT_MAP", {})
        if not tenant_map:
            return None
        host = request.get_host().split(":")[0]
        empresa_id = tenant_map.get(host)
        if not empresa_id:
            return None
        from taller.models import Empresa
        return Empresa.objects.filter(pk=empresa_id).first()
