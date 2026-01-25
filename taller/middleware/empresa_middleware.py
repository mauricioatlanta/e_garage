# Middleware que añade la empresa al request según el usuario logueado
from __future__ import annotations

from django.shortcuts import redirect


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

        if getattr(request, "user", None) is not None and request.user.is_authenticated:
            try:
                # Asumiendo relación OneToOne/ForeignKey desde User -> Empresa
                request.empresa = getattr(request.user, "empresa", None)

                # Verificar si la suscripción está vencida
                if (
                    request.empresa
                    and getattr(request.empresa, "debe_bloquear", False)
                    and not self.is_exempt_url(request.path)
                ):
                    return redirect("suspension")

            except Exception:
                # Evita romper todo el request por un edge case.
                request.empresa = None

        return self.get_response(request)

    def is_exempt_url(self, path: str) -> bool:
        """URLs que no requieren suscripción activa"""

        # Rutas base (sin prefijos /cl/es/ o /us/en/ etc.)
        exempt_bases = [
            "/suspension/",
            "/accounts/logout/",
            "/accounts/login/",
            "/admin/",
            "/analytics/",  # dashboard analytics
            "/static/",
            "/media/",
            "/comprobante-pago/",
            "/robots.txt",
            "/favicon.ico",
        ]

        # Normaliza /<pais>/<idioma>/... -> /...
        norm = self._strip_country_locale_prefix(path)

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
