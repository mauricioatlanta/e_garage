from django.contrib import messages
from django.shortcuts import redirect

from taller.utils.login_exempt import is_login_exempt_path
from taller.utils.empresa import get_user_empresa_safe


class _VerificarSuscripcionMiddlewareLegacy:
    """
    Middleware de bloqueo suave para empresas con suscripción vencida.

    Bloquea acceso a usuarios con suscripción vencida excepto en rutas whitelisted.
    Redirige a una página de renovación/billing con mensaje informativo.
    """

    # Rutas exentas (login vía helper común is_login_exempt_path)
    EXEMPT_URLS = [
        "/accounts/logout/",
        "/accounts/signup/",
        "/accounts/password/",  # reset, change, etc.
        "/billing/",
        "/soporte/",
        "/help/",
        "/admin/",  # Admin siempre accesible
        "/analytics/",  # Analytics dashboard - requiere login pero no suscripción activa
        "/static/",
        "/media/",
        "/favicon.ico",
        # APIs de documentos (GET): evitar redirect para que el formulario cargue número/repuestos
        "/us/documentos/api/",
        "/cl/documentos/api/",
    ]

    # Rutas que requieren suscripción activa pero muestran mensaje en lugar de bloquear
    WARNING_URLS = [
        "/documentos/",
        "/vehiculos/",
        "/clientes/",
        "/reportes/",
        "/settings/",  # /cl/es/settings/, /us/en/settings/, etc.
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo procesar usuarios autenticados
        if request.user.is_authenticated:
            # Staff/superuser no deben quedar bloqueados por suscripción de empresa
            if request.user.is_staff or request.user.is_superuser:
                return self.get_response(request)

            empresa = getattr(request, "empresa", None)

            if empresa and empresa.debe_bloquear:
                # Verificar si la ruta está exenta
                if self._is_exempt_url(request.path):
                    return self.get_response(request)

                # Verificar si es una ruta que requiere advertencia
                if self._is_warning_url(request.path):
                    # Agregar mensaje de advertencia pero permitir acceso
                    if not messages.get_messages(request):
                        messages.warning(
                            request,
                            f"⚠️ Tu suscripción ha vencido. {empresa.get_mensaje_alerta()}",
                        )
                    return self.get_response(request)

                # Para todas las demás rutas, redirigir a billing
                return redirect(self._get_billing_url(request))

        return self.get_response(request)

    def _is_exempt_url(self, path):
        """Verifica si la URL está en la lista de exenciones (login vía helper común)"""
        if (path or "").rstrip("/") == "":
            return True  # Raíz: landing selector de país
        if is_login_exempt_path(path):
            return True
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            return True
        if "/documentos/api/" in path:
            return True
        return False

    def _is_warning_url(self, path):
        """Verifica si la URL requiere advertencia pero no bloqueo"""
        if any(path.startswith(url) for url in self.WARNING_URLS):
            return True
        # Prefijos país/idioma: /cl/es/settings/ → resto /settings/
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and len(parts[0]) == 2 and len(parts[1]) == 2:
            tail = "/" + "/".join(parts[2:])
            if tail.startswith("/settings/") or tail.rstrip("/") == "/settings":
                return True
        return False

    def _get_billing_url(self, request):
        """Obtiene la URL de billing apropiada según el país"""
        # Nunca usar getattr(user, "empresa", None): el descriptor OneToOne lanza si no hay empresa.
        empresa = get_user_empresa_safe(request.user)
        if empresa is None:
            empresa = getattr(request, "empresa", None)

        if empresa and empresa.pais == "US":
            # URL para USA
            return "/us/billing/renew/"
        else:
            # URL para Chile (default)
            return "/cl/billing/renew/"


from django.http import HttpResponseForbidden, JsonResponse

from taller.services.subscription_access_service import SubscriptionAccessService


class VerificarSuscripcionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        empresa = getattr(request, "empresa", None)
        request.subscription_state = "active"
        request.subscription_access_reason = None
        request.billing_renew_url = SubscriptionAccessService.get_billing_url(empresa)

        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_staff or request.user.is_superuser:
            return self.get_response(request)

        decision = SubscriptionAccessService.decide(
            empresa=empresa,
            path=request.path,
            method=request.method,
        )

        request.subscription_state = decision.state
        request.subscription_access_reason = decision.reason
        request.billing_renew_url = SubscriptionAccessService.get_billing_url(empresa)

        if decision.allow:
            return self.get_response(request)

        self._add_subscription_message(request, decision)

        if request.method.upper() != "GET" and self._is_api_request(request):
            return JsonResponse(
                {
                    "detail": self._get_message_text(request, decision),
                    "subscription_state": decision.state,
                    "reason": decision.reason,
                    "redirect_to": decision.redirect_to,
                },
                status=403,
            )

        if decision.redirect_to:
            return redirect(decision.redirect_to)

        return HttpResponseForbidden(self._get_message_text(request, decision))

    @staticmethod
    def _is_api_request(request) -> bool:
        requested_with = request.headers.get("X-Requested-With", "")
        accept = request.headers.get("Accept", "")
        content_type = request.headers.get("Content-Type", "")
        return (
            requested_with == "XMLHttpRequest"
            or "application/json" in accept
            or "application/json" in content_type
            or "/api/" in request.path
        )

    def _add_subscription_message(self, request, decision) -> None:
        if getattr(request, "_messages", None) is None:
            return

        message_text = self._get_message_text(request, decision)
        if not message_text or self._has_message(request, message_text):
            return

        messages.add_message(request, self._get_message_level(decision), message_text)

    @staticmethod
    def _has_message(request, message_text: str) -> bool:
        storage = getattr(request, "_messages", None)
        if storage is None:
            return False

        existing_messages = [str(message) for message in getattr(storage, "_queued_messages", [])]
        existing_messages.extend(
            str(message) for message in getattr(storage, "_loaded_messages", [])
        )
        return message_text in existing_messages

    @staticmethod
    def _get_message_level(decision) -> int:
        if decision.state == "blocked":
            return messages.ERROR
        return messages.WARNING

    def _get_message_text(self, request, decision) -> str:
        is_english = getattr(request, "LANGUAGE_CODE", "") == "en"

        if decision.state == "grace":
            if is_english:
                return "Your subscription expired, but you are still within the grace period."
            return "Tu suscripcion vencio, pero sigues dentro del periodo de gracia."

        if decision.state == "restricted":
            if decision.reason == "restricted_write_block":
                if is_english:
                    return "This action is blocked until you renew your subscription."
                return "Esta accion esta bloqueada hasta que renueves tu suscripcion."
            if is_english:
                return "Some modules are restricted until you renew your subscription."
            return "Algunos modulos estan restringidos hasta que renueves tu suscripcion."

        if is_english:
            return "Your account is suspended due to an overdue subscription. Renew to recover full access."
        return "Tu cuenta esta suspendida por una suscripcion vencida. Renueva para recuperar el acceso completo."
