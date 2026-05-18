"""
Middleware de Control de Suscripción Profesional

Gestiona el acceso a funcionalidades según el estado de suscripción.
Redirige usuarios con suscripción suspendida ('unpaid') a pantalla de pago.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpRequest


class ControlSuscripcionMiddleware:
    """Controla acceso basado en estado de suscripción."""

    RUTAS_PERMITIDAS = [
        'admin:index',
        'admin:logout',
        'account_logout',
        'pantalla_pago',
        'suspension',
    ]

    PREFIJOS_EXENTOS = [
        '/admin/',
        '/accounts/logout/',
        '/static/',
        '/media/',
        '/robots.txt',
        '/favicon.ico',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        """Procesa cada request y valida estado de suscripción."""
        
        # Solo procesar usuarios autenticados
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Obtener empresa del usuario
        empresa = getattr(request, 'empresa', None)

        # Si no hay empresa asociada, continuar
        if not empresa:
            return self.get_response(request)

        # Verificar si la suscripción está suspendida
        if self._suscripcion_suspendida(empresa):
            # Permitir acceso a rutas exentas
            if self._es_ruta_permitida(request):
                return self.get_response(request)

            # Redirigir a pantalla de pago
            return redirect('pantalla_pago')

        return self.get_response(request)

    @staticmethod
    def _suscripcion_suspendida(empresa) -> bool:
        """Verifica si status_suscripcion es 'unpaid'."""
        return getattr(empresa, 'status_suscripcion', None) == 'unpaid'

    def _es_ruta_permitida(self, request: HttpRequest) -> bool:
        """Verifica si la ruta solicitada está permitida."""
        path = request.path

        # Verificar prefijos exentos
        for prefijo in self.PREFIJOS_EXENTOS:
            if path.startswith(prefijo):
                return True

        # Verificar rutas permitidas por nombre
        for ruta_permitida in self.RUTAS_PERMITIDAS:
            try:
                url_permitida = reverse(ruta_permitida)
                if path.startswith(url_permitida):
                    return True
            except Exception:
                pass

        return False
