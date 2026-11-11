from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
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
        request.user = AnonymousUser()
        match = resolve(request.path)
        response = match.func(request, **match.kwargs)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/br/pt/reportes/?periodo=mes")
