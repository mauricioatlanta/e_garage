"""
EmpresaResolverMiddleware

Inyecta request.empresa resolviendo correctamente tanto owners (OneToOne)
como team members (TeamMember.is_active=True).

Reemplaza el comportamiento de SingleUserPerEmpresaMiddleware, que bloqueaba
a cualquier usuario que no fuera el owner directo. Este middleware permite
multi-usuario dentro del cupo del plan.

Posición en el stack: después de AuthenticationMiddleware.
"""

from django.contrib.auth import logout
from django.shortcuts import redirect

from taller.utils.empresa import get_user_empresa_safe

EXEMPT_PREFIXES = (
    "/admin/",
    "/accounts/",
    "/static/",
    "/media/",
    "/robots.txt",
    "/favicon.ico",
)


class EmpresaResolverMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa = None
        request.company = None
        request.country = None

        if request.user.is_authenticated:
            empresa = get_user_empresa_safe(request.user)
            if empresa is not None:
                request.empresa = empresa
                request.company = empresa
                request.country = getattr(empresa, "pais", None)
            elif not self._is_exempt(request.path):
                # Usuario autenticado sin empresa ni membership activo → logout limpio.
                # Esto cubre cuentas huérfanas o memberships desactivados.
                logout(request)
                return redirect("account_login")

        return self.get_response(request)

    @staticmethod
    def _is_exempt(path: str) -> bool:
        return any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES)
