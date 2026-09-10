from django.shortcuts import redirect

from taller.services.onboarding_service import OnboardingService, onboarding_step_url


class OnboardingMiddleware:
    """
    Middleware que redirige automáticamente a usuarios que no han completado el onboarding
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_superuser or request.user.is_staff:
            return self.get_response(request)

        path = request.path or "/"

        if self._is_allowed_during_onboarding(path):
            return self.get_response(request)

        empresa = getattr(request, "empresa", None)
        try:
            direct_empresa = getattr(request.user, "empresa", None)
        except Exception:
            direct_empresa = None
        empresa = empresa or direct_empresa

        if not empresa:
            return self.get_response(request)

        if getattr(empresa, "onboarding_completado", False):
            return self.get_response(request)

        OnboardingService.mark_started(empresa)
        step = OnboardingService.normalize_step(getattr(empresa, "onboarding_step", 1)) or 1
        return redirect(onboarding_step_url(request, empresa, step))

    @staticmethod
    def _strip_country_prefix(path):
        parts = [p for p in (path or "/").split("/") if p]
        if len(parts) >= 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
            return "/" + "/".join(parts[2:]) + ("/" if path.endswith("/") else "")
        if len(parts) >= 1 and parts[0] in {"cl", "us", "ar", "uy", "mx", "pe", "co", "ec", "br", "ve"}:
            return "/" + "/".join(parts[1:]) + ("/" if path.endswith("/") else "")
        return path or "/"

    @classmethod
    def _is_allowed_during_onboarding(cls, path):
        base_path = cls._strip_country_prefix(path)
        allowed_prefixes = (
            "/accounts/",
            "/login/",
            "/logout/",
            "/password_reset/",
            "/reset/",
            "/onboarding/",
            "/static/",
            "/media/",
            "/help/",
            "/ayuda/",
            "/soporte/",
            "/i18n/",
            "/jsi18n/",
            "/health/",
            "/healthz/",
            "/health-simple/",
            "/legal/",
            "/changelog/",
            "/webhooks/",
        )
        if base_path in {"/", ""}:
            return True
        return any(base_path.startswith(prefix) for prefix in allowed_prefixes)
