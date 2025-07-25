from django.shortcuts import redirect
from django.urls import reverse

class SuscripcionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            empresa = getattr(request, "empresa", None)
            if empresa and empresa.debe_bloquear:
                return redirect(reverse("suscripcion_bloqueada"))
        return self.get_response(request)
