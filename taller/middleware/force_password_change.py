from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from taller.auth.password_policy import user_must_change_password


class ForcePasswordChangeMiddleware:
    """
    Bloquea navegación operacional hasta que el usuario cambie una clave temporal.
    """

    WARNING = "Por tu seguridad, debes definir una contraseña nueva y personal antes de continuar"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if not user_must_change_password(user):
            return self.get_response(request)

        path = request.path or "/"
        if self._is_allowed_path(path):
            return self.get_response(request)

        messages.warning(request, self.WARNING)
        return redirect(self._change_password_url(request))

    def _is_allowed_path(self, path: str) -> bool:
        allowed_prefixes = (
            getattr(settings, "STATIC_URL", "/static/"),
            getattr(settings, "MEDIA_URL", "/media/"),
            "/static/",
            "/media/",
            "/accounts/logout/",
            "/cl/es/accounts/logout/",
            "/us/en/accounts/logout/",
            "/us/es/accounts/logout/",
        )
        if any(path.startswith(prefix) for prefix in allowed_prefixes if prefix):
            return True

        allowed_exact = {
            "/accounts/password/force/",
            "/cl/es/accounts/password/force/",
            "/us/en/accounts/password/force/",
            "/us/es/accounts/password/force/",
        }
        return path in allowed_exact

    def _change_password_url(self, request) -> str:
        path = request.path or ""
        if path.startswith("/cl/es/"):
            return "/cl/es/accounts/password/force/"
        if path.startswith("/us/en/"):
            return "/us/en/accounts/password/force/"
        if path.startswith("/us/es/"):
            return "/us/es/accounts/password/force/"
        try:
            return reverse("force_password_change")
        except Exception:
            return "/accounts/password/force/"
