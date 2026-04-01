# Middleware que añade la empresa al request según el usuario logueado
from __future__ import annotations

from django.db.utils import OperationalError
from django.shortcuts import redirect

from taller.utils.login_exempt import is_login_exempt_path
from taller.utils.empresa import get_user_empresa_safe


class EmpresaMiddleware:
    """
    Middleware multi-tenant:
    - Inyecta request.empresa desde request.user.empresa (si existe)
    - Bloquea acceso si la suscripción está vencida (excepto URLs exentas)

    Nota: NO importamos modelos aquí para evitar AppRegistryNotReady en el arranque.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa = None
        request.company = None
        request.country = None

        if getattr(request, "user", None) is not None and request.user.is_authenticated:
            try:
                # Asumiendo relación OneToOne/ForeignKey desde User -> Empresa.
                # OperationalError (ej. columna is_trial faltante) no debe devolver 500.
                # No usar getattr(user, "empresa", None): sin fila relacionada lanza RelatedObjectDoesNotExist.
                request.empresa = get_user_empresa_safe(request.user)
                request.company = request.empresa
                request.country = (
                    getattr(request.empresa, "pais", None) if request.empresa else None
                )

                # Verificar si la suscripción está vencida
                if (
                    request.empresa
                    and getattr(request.empresa, "debe_bloquear", False)
                    and not (request.user.is_staff or request.user.is_superuser)
                    and not self.is_exempt_url(request.path)
                ):
                    return redirect("suspension")

            except (Exception, OperationalError):
                # Evita 500 por DB desactualizada (ej. is_trial faltante) u otros edge cases.
                request.empresa = None
                request.company = None
                request.country = None

        return self.get_response(request)

    def is_exempt_url(self, path: str) -> bool:
        """URLs que no requieren suscripción activa (login vía helper común)"""
        if is_login_exempt_path(path):
            return True

        exempt_bases = [
            "/suspension/",
            "/accounts/logout/",
            "/admin/",
            "/analytics/",
            "/static/",
            "/media/",
            "/comprobante-pago/",
            "/robots.txt",
            "/favicon.ico",
        ]
        norm = self._strip_country_locale_prefix(path)
        # /cl/es/settings/ → /settings — permitir centro de ajustes aunque suscripción esté vencida
        if norm.startswith("/settings"):
            return True
        # APIs de documentos: el formulario necesita obtener número aunque suscripción esté vencida
        if "/documentos/api/" in path or norm.startswith("/documentos/api/"):
            return True
        # APIs de ajax (buscar clientes, vehículos, repuestos)
        if "/ajax/" in path or norm.startswith("/ajax/"):
            return True
        return any(path.startswith(u) for u in exempt_bases) or any(
            norm.startswith(u) for u in exempt_bases
        )

    @staticmethod
    def _strip_country_locale_prefix(path: str) -> str:
        """
        Convierte:
          /cl/es/centro-operaciones/ -> /centro-operaciones/
          /us/en/bienvenida/        -> /bienvenida/
        Si no calza, devuelve path tal cual.
        """
        parts = path.split("/")
        # parts: ["", "cl", "es", "centro-operaciones", ""]
        if len(parts) >= 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
            rest = "/" + "/".join(parts[3:])
            # evitar '//' accidental
            return rest.replace("//", "/")
        return path
