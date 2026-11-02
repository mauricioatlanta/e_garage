from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.utils import timezone

from taller.middleware.trust import TrustMiddleware
from taller.models import SesionUsuario
from taller.utils.trust import detect_shared_account, mark_inactive_sessions

User = get_user_model()


class TrustFoundationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="trust-user",
            email="trust@example.com",
            password="test-pass-123",
        )
        self.factory = RequestFactory()

    def _request(self, path="/cl/es/workspace/"):
        request = self.factory.get(
            path,
            HTTP_USER_AGENT="Mozilla/5.0 Chrome/120.0",
            HTTP_ACCEPT_LANGUAGE="es-CL,es;q=0.9",
            HTTP_ACCEPT_ENCODING="gzip, deflate, br",
        )
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request.user = self.user
        request.empresa = None
        request.country = "CL"
        return request

    def test_first_authenticated_request_creates_session_with_one_page(self):
        request = self._request()
        middleware = TrustMiddleware(lambda req: type("Response", (), {})())

        middleware(request)

        tracked = SesionUsuario.objects.get(session_key=request.session.session_key)
        self.assertEqual(tracked.usuario, self.user)
        self.assertEqual(tracked.paginas_visitadas, 1)
        self.assertTrue(tracked.activa)
        self.assertEqual(tracked.pais, "CL")

    def test_static_request_is_not_tracked(self):
        request = self._request("/static/app.css")
        middleware = TrustMiddleware(lambda req: type("Response", (), {})())

        middleware(request)

        self.assertFalse(SesionUsuario.objects.exists())

    def test_pending_pages_flush_on_logout(self):
        request = self._request()
        tracked = SesionUsuario.objects.create(
            usuario=self.user,
            session_key=request.session.session_key,
            device_fingerprint="a" * 64,
            ip="127.0.0.1",
            paginas_visitadas=1,
            activa=True,
        )
        request.session["_trust"] = {"pending": 4, "last_flush": 0}
        request.session.save()

        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user,
        )

        tracked.refresh_from_db()
        self.assertEqual(tracked.paginas_visitadas, 5)
        self.assertFalse(tracked.activa)

    def test_cleanup_marks_stale_sessions_inactive(self):
        stale = SesionUsuario.objects.create(
            usuario=self.user,
            session_key="stale-session",
            device_fingerprint="b" * 64,
            ip="127.0.0.1",
            ultima_actividad=timezone.now() - timedelta(minutes=31),
            activa=True,
        )

        updated = mark_inactive_sessions()

        stale.refresh_from_db()
        self.assertEqual(updated, 1)
        self.assertFalse(stale.activa)

    def test_shared_account_detects_two_fingerprints(self):
        now = timezone.now()
        SesionUsuario.objects.create(
            usuario=self.user,
            session_key="session-one",
            device_fingerprint="c" * 64,
            ip="127.0.0.1",
            paginas_visitadas=3,
            ultima_actividad=now,
            activa=True,
        )
        SesionUsuario.objects.create(
            usuario=self.user,
            session_key="session-two",
            device_fingerprint="d" * 64,
            ip="127.0.0.2",
            paginas_visitadas=3,
            ultima_actividad=now,
            activa=True,
        )

        flag = detect_shared_account(self.user)

        self.assertIsNotNone(flag)
        self.assertEqual(flag["reason"], "concurrent_devices")
        self.assertEqual(flag["distinct_fingerprints"], 2)

    def test_cleanup_command_runs(self):
        with patch(
            "taller.management.commands.trust_cleanup.mark_inactive_sessions",
            return_value=2,
        ):
            call_command("trust_cleanup")
