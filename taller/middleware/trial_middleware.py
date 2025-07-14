from django.shortcuts import redirect
from django.urls import reverse
from taller.models.trial import TrialRegistro
from django.utils import timezone

class TrialAccessMiddleware:
    """
    Middleware que restringe el acceso a la app según el estado de la prueba (trial).
    Si la prueba no está activa o está expirada, redirige a la activación o registro.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Permitir acceso libre a rutas de registro, activación, login, admin y estáticos
        allowed_paths = [
            '/',
            reverse('registro_trial'),
            reverse('activar_trial'),
            reverse('login'),
            '/admin/', '/accounts/', '/static/', '/media/'
        ]
        if any(request.path == p or request.path.startswith(p) for p in allowed_paths):
            return self.get_response(request)

        # Chequear si hay una prueba activa y no expirada
        email = request.session.get('trial_email')
        if email:
            try:
                trial = TrialRegistro.objects.get(email=email)
                trial.expirar_si_corresponde()
                if trial.prueba_activa and not trial.prueba_expirada:
                    return self.get_response(request)
                elif trial.prueba_expirada:
                    return redirect('activar_trial')
            except TrialRegistro.DoesNotExist:
                pass
        # Si no hay sesión de trial, redirigir a registro
        return redirect('registro_trial')
