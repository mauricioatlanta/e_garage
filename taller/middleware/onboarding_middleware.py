from django.conf import settings
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

        path = request.path or "/"

        default_cc = (getattr(settings, "EGARAGE_DEFAULT_COUNTRY", "cl") or "cl").strip("/")
        default_lang = (getattr(settings, "EGARAGE_DEFAULT_LANG", "es") or "es").strip("/")
        default_prefix = f"/{default_cc}/{default_lang}"

        prefix = ""
        try:
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                prefix = f"/{parts[0]}/{parts[1]}" if len(parts[1]) == 2 else ""
        except Exception:
            prefix = ""

        if path.startswith("/onboarding/") and not prefix:
            return redirect(f"{default_prefix}{path}")

        # 1. EXCLUIR SI ES UNA PETICIÓN AJAX (XHR) O API
        if (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or path.startswith("/api/")
            or path.startswith("/webhooks/")
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
            "/login/",
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
            if path.startswith(excluded) or (prefix and path.startswith(prefix + excluded)):
                return self.get_response(request)

        base_path = path
        if prefix and path.startswith(prefix):
            base_path = path[len(prefix) :] or "/"

        protected_paths = (
            "/dashboard/",
            "/workspace/",
            "/settings/",
            "/centro-operaciones/",
            "/centro-operaciones-espacial/",
        )

        is_protected = any(base_path.startswith(p) for p in protected_paths)
        if not is_protected:
            return self.get_response(request)

        # Verificar si el usuario tiene empresa activa (Multi-tenant aware)
        try:
            from taller.utils.empresa import get_active_empresa

            empresa = get_active_empresa(request)
            if not empresa:
                return self.get_response(request)
        except Exception:
            return self.get_response(request)

        if not empresa:
            if not base_path.startswith("/configuracion/"):
                try:
                    return redirect("taller:configuracion")
                except Exception:
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
        if not path.startswith("/onboarding/") and not (
            prefix and path.startswith(f"{prefix}/onboarding/")
        ):
            # Marcar inicio del onboarding si no está marcado
            if not empresa.onboarding_started_at:
                from django.utils import timezone

                empresa.onboarding_started_at = timezone.now()
                empresa.save(update_fields=["onboarding_started_at"])

            # Mapeo de pasos a URLs reales
            step_map = {
                1: "identidad",
                2: "finalizar",
                3: "finalizar",
            }
            step_name = step_map.get(getattr(empresa, "onboarding_step", 1), "identidad")

            # Redirigir al paso actual usando la nueva ruta
            return redirect(
                f"{prefix}/onboarding/{step_name}/"
                if prefix
                else f"{default_prefix}/onboarding/{step_name}/"
            )

        return self.get_response(request)
