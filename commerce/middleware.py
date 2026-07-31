"""
CommerceTenantMiddleware

Resuelve el tenant Commerce (Empresa) a partir del hostname del request.
Setea request.commerce_empresa si el host está en COMMERCE_TENANT_MAP.

Configuración en settings (ejemplo):
    COMMERCE_TENANT_MAP = {
        "monteazul.local": 1,   # empresa_id
        "monteazul.cl": 1,
    }

En producción, Nginx puede rutear monteazul.cl al mismo Django.
El middleware resuelve el tenant y Commerce sirve el catálogo correcto.
"""
from django.conf import settings


class CommerceTenantMiddleware:

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        request.commerce_empresa = self._resolve_tenant(request)
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
