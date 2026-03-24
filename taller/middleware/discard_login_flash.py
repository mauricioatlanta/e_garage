"""
Vacía la cola de django.contrib.messages en GET de páginas de login (usuario anónimo).

Así no reaparecen en el primer panel tras iniciar sesión mensajes viejos
(facturas, idioma, desarme, cierre de sesión, etc.).
"""

from django.contrib.messages import get_messages


def _is_login_get(request) -> bool:
    if request.method != "GET":
        return False
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return False
    path = (request.path or "").lower().rstrip("/")
    if path.endswith("/login"):
        return True
    if "/accounts/login" in path:
        return True
    return False


class DiscardLoginFlashMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_login_get(request):
            list(get_messages(request))
        return self.get_response(request)
