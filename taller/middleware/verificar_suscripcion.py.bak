from django.contrib import messages
from django.shortcuts import redirect

from taller.utils.login_exempt import is_login_exempt_path


class VerificarSuscripcionMiddleware:
    """
    Middleware de bloqueo suave para empresas con suscripción vencida.

    Bloquea acceso a usuarios con suscripción vencida excepto en rutas whitelisted.
    Redirige a una página de renovación/billing con mensaje informativo.
    """

    # Rutas exentas (login vía helper común is_login_exempt_path)
    EXEMPT_URLS = [
        "/accounts/logout/",
        "/accounts/signup/",
        "/accounts/password/",  # reset, change, etc.
        "/billing/",
        "/soporte/",
        "/help/",
        "/admin/",  # Admin siempre accesible
        "/analytics/",  # Analytics dashboard - requiere login pero no suscripción activa
        "/static/",
        "/media/",
        "/favicon.ico",
        # APIs de documentos (GET): evitar redirect para que el formulario cargue número/repuestos
        "/us/documentos/api/",
        "/cl/documentos/api/",
    ]

    # Rutas que requieren suscripción activa pero muestran mensaje en lugar de bloquear
    WARNING_URLS = [
        "/documentos/",
        "/vehiculos/",
        "/clientes/",
        "/reportes/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo procesar usuarios autenticados
        if request.user.is_authenticated:
            empresa = getattr(request, "empresa", None)

            if empresa and empresa.debe_bloquear:
                # Verificar si la ruta está exenta
                if self._is_exempt_url(request.path):
                    return self.get_response(request)

                # Verificar si es una ruta que requiere advertencia
                if self._is_warning_url(request.path):
                    # Agregar mensaje de advertencia pero permitir acceso
                    if not messages.get_messages(request):
                        messages.warning(
                            request,
                            f"⚠️ Tu suscripción ha vencido. {empresa.get_mensaje_alerta()}",
                        )
                    return self.get_response(request)

                # Para todas las demás rutas, redirigir a billing
                return redirect(self._get_billing_url(request))

        return self.get_response(request)

    def _is_exempt_url(self, path):
        """Verifica si la URL está en la lista de exenciones (login vía helper común)"""
        if (path or "").rstrip("/") == "":
            return True  # Raíz: landing selector de país
        if is_login_exempt_path(path):
            return True
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            return True
        if "/documentos/api/" in path:
            return True
        return False

    def _is_warning_url(self, path):
        """Verifica si la URL requiere advertencia pero no bloqueo"""
        return any(path.startswith(url) for url in self.WARNING_URLS)

    def _get_billing_url(self, request):
        """Obtiene la URL de billing apropiada según el país"""
        empresa = getattr(request.user, "empresa", None)

        if empresa and empresa.pais == "US":
            # URL para USA
            return "/us/billing/renew/"
        else:
            # URL para Chile (default)
            return "/cl/billing/renew/"
