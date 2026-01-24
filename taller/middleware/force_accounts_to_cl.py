"""
Redirige /accounts/login/ → /cl/accounts/login/ para que el login sin país
use siempre Chile por defecto y no dependa de sesión (p. ej. preferred_country=UY).

Debe ir después de SessionMiddleware.
"""

from django.shortcuts import redirect


class ForceAccountsToCLMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.rstrip("/") == "/accounts/login":
            url = "/cl/accounts/login/"
            if request.GET:
                url = f"{url}?{request.GET.urlencode()}"
            return redirect(url)
        return self.get_response(request)
