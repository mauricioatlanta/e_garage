"""
EmpresaResolverMiddleware

Inyecta request.empresa resolviendo correctamente tanto owners (OneToOne)
como team members (TeamMember.is_active=True).

Reemplaza el comportamiento de SingleUserPerEmpresaMiddleware, que bloqueaba
a cualquier usuario que no fuera el owner directo. Este middleware permite
multi-usuario dentro del cupo del plan.

Posición en el stack: después de HostTenantMiddleware (que lo precede desde Fase 2).

Lógica:
    A) Si request.empresa ya viene poblado (dominio personalizado resuelto por
       HostTenantMiddleware):
         - Usuario anónimo → acceso permitido (empresa ya fijada por host).
         - Usuario autenticado del MISMO tenant → acceso permitido.
         - Usuario autenticado de OTRO tenant → logout + redirect a login.
    B) Si request.empresa es None (acceso por egarage.cl o dominio no reconocido):
         - Comportamiento original: resolver empresa desde el usuario.
"""

from django.contrib.auth import logout
from django.shortcuts import redirect

from taller.utils.empresa import get_user_empresa_safe
from taller.utils.login_exempt import is_login_exempt_path


class EmpresaResolverMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # HostTenantMiddleware puede haber poblado request.empresa desde el host.
        # Solo inicializamos los atributos si aún no existen.
        if not hasattr(request, "empresa"):
            request.empresa = None
            request.company = None
            request.country = None

        # ── A) Dominio personalizado ya resuelto ──────────────────────────────
        if getattr(request, "empresa", None) is not None:
            if request.user.is_authenticated:
                user_empresa = get_user_empresa_safe(request.user)
                if user_empresa is None or user_empresa.pk != request.empresa.pk:
                    logout(request)
                    return redirect("account_login")
            return self.get_response(request)

        # ── B) Ruta normal (egarage.cl): comportamiento original ──────────────
        if request.user.is_authenticated:
            empresa = get_user_empresa_safe(request.user)
            if empresa is not None:
                request.empresa = empresa
                request.company = empresa
                request.country = getattr(empresa, "pais", None)
            elif not self._is_exempt(request.path):
                # Usuario autenticado sin empresa ni membership activo → logout.
                logout(request)
                return redirect("account_login")

        return self.get_response(request)

    @staticmethod
    def _is_exempt(path: str) -> bool:
        return is_login_exempt_path(path)
