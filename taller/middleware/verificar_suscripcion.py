from django.core.exceptions import ImproperlyConfigured
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
            "/admin/",
            "/accounts/login/",
            "/accounts/logout/",
            "/cl/accounts/login/",
            "/us/accounts/login/",
            "/cl/accounts/logout/",
            "/us/accounts/logout/",
            "/cl/login/",
            "/us/login/",
            "/login/",
            "/logout/",
        ]

        # Try to get the suscripcion_bloqueada URL, but handle if it doesn't exist
        try:
            suscripcion_url = reverse("suscripcion_bloqueada")
            allowed_paths.append(suscripcion_url)
        except:
            # If the URL doesn't exist, use a fallback path
            suscripcion_url = "/suscripcion-bloqueada/"
            allowed_paths.append(suscripcion_url)

        # Check if current path is allowed
        if request.path in allowed_paths or request.path.startswith("/admin/"):
            return self.get_response(request)

        user = request.user
        if user.is_authenticated:
            suscripcion = getattr(user, "suscripcion", None)
            if not suscripcion or not suscripcion.activa or suscripcion.esta_vencida():
                try:
                    return redirect("suscripcion_bloqueada")
                except:
                    # Fallback to direct URL if reverse fails
                    return redirect("/suscripcion-bloqueada/")
        return self.get_response(request)
