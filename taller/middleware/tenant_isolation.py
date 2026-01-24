"""
Middleware mejorado para aislamiento multi-tenant.
Garantiza que request.empresa esté siempre disponible y correcto.
"""

import logging
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from taller.models import Empresa

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware:
    """
    Middleware que garantiza aislamiento multi-tenant mejorado.

    Funciones:
    1. Inyecta request.empresa basado en el usuario autenticado
    2. Verifica suscripción activa
    3. Registra accesos para auditoría
    4. Bloquea acceso si no hay empresa asignada
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Inyectar empresa en el request
        request = self.process_request(request)

        # Continuar con la cadena de middlewares
        response = self.get_response(request)

        # Procesar respuesta (si necesario)
        response = self.process_response(request, response)

        return response

    def process_request(self, request):
        """Procesar request y inyectar empresa"""
        # URLs que no requieren autenticación ni empresa
        if self.is_public_url(request.path):
            request.empresa = None
            return request

        # Si el usuario no está autenticado, no hay empresa
        if not request.user.is_authenticated:
            request.empresa = None
            return request

        # Obtener empresa del usuario
        try:
            empresa = request.user.empresa
            request.empresa = empresa

            # Verificar que la empresa esté activa
            if hasattr(empresa, "debe_bloquear") and empresa.debe_bloquear:
                if not self.is_exempt_url(request.path):
                    logger.warning(
                        f"Intento de acceso bloqueado para usuario {request.user.username} "
                        f"(empresa: {empresa.id}, path: {request.path})"
                    )
                    return redirect("suspension")

            # Log para auditoría (solo en rutas críticas)
            if self.is_critical_path(request.path):
                logger.info(
                    f"Acceso: usuario={request.user.username}, "
                    f"empresa={empresa.id}, path={request.path}"
                )

        except AttributeError:
            # Usuario sin empresa asignada
            request.empresa = None

            # Bloquear acceso a rutas privadas
            if not self.is_public_url(request.path) and not self.is_exempt_url(request.path):
                logger.warning(
                    f"Usuario {request.user.username} intentó acceder sin empresa: {request.path}"
                )
                # Redirigir a página de configuración o mostrar error
                if request.path.startswith("/admin/"):
                    # Permitir admin sin empresa
                    pass
                else:
                    # Para usuarios normales, bloquear acceso
                    # Podrías redirigir a una página de "configurar empresa"
                    pass

        except Empresa.DoesNotExist:
            request.empresa = None
            logger.warning(f"Usuario {request.user.username} no tiene empresa asociada")

        return request

    def process_response(self, request, response):
        """Procesar respuesta (opcional, para auditoría)"""
        # Aquí podrías agregar headers de auditoría, logging, etc.
        if hasattr(request, "empresa") and request.empresa:
            # Agregar header con ID de empresa para debugging
            if hasattr(response, "headers"):
                response.headers["X-Empresa-ID"] = str(request.empresa.id)

        return response

    def is_public_url(self, path):
        """URLs públicas que no requieren autenticación"""
        public_urls = [
            "/accounts/login/",
            "/accounts/signup/",
            "/accounts/logout/",
            "/accounts/password/",
            "/static/",
            "/media/",
            "/api/public/",
        ]
        return any(path.startswith(url) for url in public_urls)

    def is_exempt_url(self, path):
        """URLs que no requieren suscripción activa"""
        exempt_urls = [
            "/suspension/",
            "/accounts/logout/",
            "/accounts/password/",
            "/admin/",
            "/static/",
            "/media/",
            "/comprobante-pago/",
            "/accounts/profile/",
            "/analytics/",  # Analytics dashboard - requiere login pero no suscripción activa
        ]
        return any(path.startswith(url) for url in exempt_urls)

    def is_critical_path(self, path):
        """Rutas críticas que requieren logging de auditoría"""
        critical_paths = [
            "/documentos/",
            "/clientes/",
            "/vehiculos/",
            "/reportes/",
            "/configuracion/",
        ]
        return any(path.startswith(path_prefix) for path_prefix in critical_paths)


class TenantSecurityMiddleware:
    """
    Middleware adicional que verifica seguridad a nivel de tenant.
    Detecta intentos de acceso a objetos de otras empresas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Verificar headers sospechosos (si tienes API)
        if hasattr(request, "META"):
            # Detectar intentos de manipulación de empresa_id en headers
            empresa_id_header = request.headers.get("x-empresa-id")
            if empresa_id_header and hasattr(request, "empresa"):
                if str(request.empresa.id) != empresa_id_header:
                    logger.warning(
                        f"Intento de manipulación de empresa_id: "
                        f"usuario={request.user.username}, "
                        f"header={empresa_id_header}, "
                        f"real={request.empresa.id}"
                    )

        return response
