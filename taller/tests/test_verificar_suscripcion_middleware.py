import json
from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from taller.middleware.verificar_suscripcion import VerificarSuscripcionMiddleware
from taller.models.empresa import Empresa


class VerificarSuscripcionMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = VerificarSuscripcionMiddleware(lambda request: HttpResponse("ok"))
        self._user_index = 0

    def _create_empresa(
        self,
        *,
        days_offset: int,
        suscripcion_activa: bool,
        pais: str = "CL",
        is_staff: bool = False,
    ):
        from taller.tests.factories import EmpresaFactory, UserFactory
        self._user_index += 1
        user = UserFactory(is_staff=is_staff)
        empresa = EmpresaFactory(user=user, nombre_taller=f"Empresa {self._user_index}", pais=pais)
        empresa.fecha_fin = timezone.now() + timedelta(days=days_offset)
        empresa.suscripcion_activa = suscripcion_activa
        empresa.save()
        return user, empresa

    def _build_request(self, path: str, method: str = "GET", user=None, empresa=None, **headers):
        request_factory = getattr(self.factory, method.lower())
        request = request_factory(path, **headers)
        request.user = user or AnonymousUser()
        request.empresa = empresa
        request.LANGUAGE_CODE = "es"

        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        return request

    def test_restricted_soft_get_is_allowed_and_sets_request_context(self):
        user, empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)
        request = self._build_request("/cl/es/servicios/", "GET", user=user, empresa=empresa)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.subscription_state, "restricted")
        self.assertEqual(request.subscription_access_reason, "restricted_soft")
        self.assertEqual(request.billing_renew_url, "/cl/es/suscripcion/pago/")

    def test_restricted_post_redirects_to_billing_and_sets_message(self):
        user, empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)
        request = self._build_request("/cl/es/servicios/", "POST", user=user, empresa=empresa)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cl/es/suscripcion/pago/")
        queued_messages = [str(message) for message in get_messages(request)]
        self.assertTrue(queued_messages)
        self.assertIn("accion", queued_messages[0].lower())

    def test_restricted_dashboard_get_redirects_to_billing(self):
        user, empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)
        request = self._build_request("/cl/es/dashboard/", "GET", user=user, empresa=empresa)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cl/es/suscripcion/pago/")
        self.assertEqual(request.subscription_state, "restricted")
        self.assertEqual(request.subscription_access_reason, "restricted_hard")

    def test_blocked_billing_page_is_allowed_and_preserves_state(self):
        user, empresa = self._create_empresa(days_offset=-45, suscripcion_activa=False)
        request = self._build_request(
            "/cl/es/suscripcion/pago/",
            "GET",
            user=user,
            empresa=empresa,
        )

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.subscription_state, "blocked")
        self.assertEqual(request.billing_renew_url, "/cl/es/suscripcion/pago/")

    def test_staff_user_bypasses_subscription_check(self):
        user, empresa = self._create_empresa(
            days_offset=-45,
            suscripcion_activa=False,
            is_staff=True,
        )
        request = self._build_request("/cl/es/dashboard/", "GET", user=user, empresa=empresa)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.subscription_state, "active")

    def test_restricted_api_post_returns_controlled_403(self):
        user, empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)
        request = self._build_request(
            "/cl/es/servicios/crear/",
            "POST",
            user=user,
            empresa=empresa,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        response = self.middleware(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(payload["subscription_state"], "restricted")
        self.assertEqual(payload["redirect_to"], "/cl/es/suscripcion/pago/")
