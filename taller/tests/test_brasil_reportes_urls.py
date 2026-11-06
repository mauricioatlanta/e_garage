from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import resolve, reverse


class BrazilReportsUrlTests(SimpleTestCase):
    def test_portuguese_reports_dashboard_is_mounted(self):
        self.assertEqual(
            reverse("brasil:reportes:reportes_dashboard"),
            "/br/pt/reportes/",
        )
        self.assertEqual(
            resolve("/br/pt/reportes/").url_name,
            "reportes_dashboard",
        )

    def test_legacy_spanish_reports_path_redirects_to_portuguese(self):
        request = RequestFactory().get("/br/es/reportes/?periodo=mes")
        match = resolve(request.path)
        response = match.func(request, **match.kwargs)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/br/pt/reportes/?periodo=mes")

    def test_brazil_does_not_render_language_switcher(self):
        request = RequestFactory().get("/br/pt/reportes/")
        request.country = "BR"
        request.LANGUAGE_CODE = "pt-br"

        html = render_to_string(
            "taller/includes/lang_switcher_cinematic.html",
            {"request": request, "LANGUAGE_CODE": "pt-br"},
        )

        self.assertNotIn("🇺🇸 EN", html)
        self.assertNotIn("🇪🇸 ES", html)

    def test_brazil_reports_dashboard_uses_portuguese_copy(self):
        request = RequestFactory().get("/br/pt/reportes/")
        request.country = "BR"
        request.LANGUAGE_CODE = "pt-br"
        request.user = AnonymousUser()
        SessionMiddleware(lambda req: HttpResponse("ok")).process_request(request)

        html = render_to_string(
            "taller/reportes/reportes.html",
            {
                "request": request,
                "LANGUAGE_CODE": "pt-br",
                "parts_reports_mode": False,
                "tire_reports_mode": False,
                "carwash_reports_mode": False,
            },
            request=request,
        )

        self.assertIn("Central de Relatórios", html)
        self.assertIn("Relatórios básicos", html)
        self.assertIn("Veículos atendidos", html)
        for untranslated_label in (
            "Basic Reports",
            "Reports Center",
            "Featured Reports",
            "Services Performed",
            "Vehicles Serviced",
            "Schedule &amp; Appointments",
            "Centro de Reportes",
            "Reportes Básicos",
            "Reportes Destacados",
            "Servicios Realizados",
            "Vehículos Atendidos",
        ):
            self.assertNotIn(untranslated_label, html)
