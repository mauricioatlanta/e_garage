"""
HostTenantMiddleware

Capa delgada que delega toda la lógica de resolución a DomainResolverService
y puebla los atributos del request cuando el host corresponde a un dominio
personalizado de un tenant.

Posición en el stack: inmediatamente después de AuthenticationMiddleware,
ANTES de EmpresaResolverMiddleware.

Toda la lógica de negocio vive en:
    taller/services/domain_resolver_service.py
"""

from taller.services.domain_resolver_service import (
    DomainResolverService,
    _SENTINEL,          # re-exportado para compatibilidad con tests existentes
)

# Aliases de módulo para que los tests unitarios existentes puedan seguir
# importando los nombres privados directamente desde este módulo.
_normalize_host             = DomainResolverService.normalize_host
_is_custom_host             = DomainResolverService.is_custom_host
_get_empresa_dominio_activo = DomainResolverService.get_for_host


class HostTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_custom_domain = False

        ed = DomainResolverService.resolve(request)
        if ed is not None:
            empresa = ed.empresa
            request.empresa          = empresa
            request.company          = empresa
            request.country          = getattr(empresa, "pais", None)
            request.is_custom_domain = True

        return self.get_response(request)
