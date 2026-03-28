from django.shortcuts import redirect
from django.urls import reverse


class OnboardingMiddleware:
    """
    Middleware que redirige automáticamente a usuarios que no han completado el onboarding
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo procesar para usuarios autenticados
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 1. EXCLUIR SI ES UNA PETICIÓN AJAX (XHR) O API
        if (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.path.startswith("/api/")
            or request.path.startswith("/webhooks/")
        ):
            return self.get_response(request)

        # Excluir rutas que no requieren onboarding completado
        excluded_paths = [
            "/admin/",
            "/logout/",
            "/password_reset/",
            "/password_reset/done/",
            "/reset/",
            "/reset/done/",
            "/accounts/",
            "/help/",
            "/ayuda/",
            "/soporte/",
            "/static/",
            "/media/",
            "/onboarding/",
            "/configuracion/",
        ]

        # Verificar si la ruta actual está excluida
        for excluded in excluded_paths:
            if request.path.startswith(excluded):
                return self.get_response(request)

        # Verificar si el usuario tiene empresa activa (Multi-tenant aware)
        try:
            from taller.utils.empresa import get_active_empresa

            empresa = get_active_empresa(request)
            if not empresa:
                raise Exception("No enterprise found")
        except:
            # Si no tiene empresa, redirigir a configuración
            if not request.path.startswith("/configuracion/"):
                try:
                    return redirect("taller:configuracion")
                except:
                    return redirect("/configuracion/")
            return self.get_response(request)

        # 2. SOLO EL DUEÑO (OWNER) DEBE HACER EL ONBOARDING
        from taller.templatetags.role_tags import is_owner

        if not is_owner(request.user):
            return self.get_response(request)

        # Si el onboarding está completado, continuar normalmente
        if getattr(empresa, "onboarding_completado", False):
            return self.get_response(request)

        # Si no está completado, redirigir al onboarding
        if not request.path.startswith("/onboarding/"):
            # Marcar inicio del onboarding si no está marcado
            if not empresa.onboarding_started_at:
                from django.utils import timezone

                empresa.onboarding_started_at = timezone.now()
                empresa.save(update_fields=["onboarding_started_at"])

            # Mapeo de pasos a URLs reales
            step_map = {
                1: "identidad",
                2: "fiscal",
                3: "finalizar",
            }
            step_name = step_map.get(getattr(empresa, "onboarding_step", 1), "identidad")

            # Redirigir al paso actual usando la nueva ruta
            return redirect(f"/onboarding/{step_name}/")

        return self.get_response(request)
