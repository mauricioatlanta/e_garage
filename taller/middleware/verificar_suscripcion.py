from django.shortcuts import redirect
from django.urls import reverse

class VerificarSuscripcionMiddleware:
    """
    Middleware que bloquea el acceso a usuarios sin suscripción activa o vencida,
    redirigiendo a la vista 'suscripcion_bloqueada'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Permitir acceso a admin, login, logout y la propia página de bloqueo
        allowed_paths = [
            reverse('suscripcion_bloqueada'),
            reverse('login'),
            reverse('logout'),
            '/admin/',
        ]
        if request.path in allowed_paths or request.path.startswith('/admin/'):
            return self.get_response(request)

        user = request.user
        if user.is_authenticated:
            suscripcion = getattr(user, 'suscripcion', None)
            if not suscripcion or not suscripcion.activa or suscripcion.esta_vencida():
                return redirect('suscripcion_bloqueada')
        return self.get_response(request)
