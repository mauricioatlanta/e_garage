import re

from django.test import TestCase
from django.urls import reverse

from taller.tests.factories import EmpresaFactory


def _html(response):
    return response.content.decode("utf-8")


def _help_context(response):
    match = re.search(r'data-help-context="([^"]+)"', _html(response))
    assert match is not None
    return match.group(1)


class AyudaContextualTests(TestCase):
    def setUp(self):
        self.empresa = EmpresaFactory(
            pais="CL",
            moneda="CLP",
            zona_horaria="America/Santiago",
            with_config=True,
        )
        self.client.force_login(self.empresa.user)

    def test_authenticated_user_sees_single_contextual_help_fab(self):
        response = self.client.get(reverse("chile:taller:team:team_list"))

        self.assertEqual(response.status_code, 200)
        html = _html(response)
        self.assertEqual(html.count('id="help-fab"'), 1)
        self.assertEqual(html.count('id="help-modal"'), 1)
        self.assertIn("openContextualHelp()", html)

    def test_team_route_uses_equipo_context_not_general(self):
        response = self.client.get(reverse("chile:taller:team:team_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "equipo")

    def test_clientes_route_uses_clientes_context(self):
        response = self.client.get(reverse("chile:clientes:lista_clientes"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "clientes")

    def test_vehiculos_route_uses_vehiculos_context(self):
        response = self.client.get(reverse("chile:vehiculos:lista_vehiculos"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "vehiculos")

    def test_documentos_route_uses_documentos_context(self):
        response = self.client.get(reverse("chile:documentos:lista_documentos"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "documentos")

    def test_documento_form_route_uses_documentos_context_without_duplicate_fab(self):
        response = self.client.get(reverse("chile:documentos:documento_crear"))

        self.assertEqual(response.status_code, 200)
        html = _html(response)
        self.assertEqual(html.count('id="help-fab"'), 1)
        self.assertEqual(_help_context(response), "documentos")

    def test_repuestos_route_uses_repuestos_context(self):
        response = self.client.get("/cl/es/repuestos/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "repuestos")

    def test_servicios_shell_has_single_fab_with_servicios_context(self):
        response = self.client.get("/cl/es/servicios/")

        self.assertEqual(response.status_code, 200)
        html = _html(response)
        self.assertEqual(html.count('id="help-fab"'), 1)
        self.assertEqual(_help_context(response), "servicios")

    def test_servicio_crear_route_uses_servicios_context(self):
        response = self.client.get("/cl/es/servicios/crear/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "servicios")

    def test_servicios_externos_route_uses_external_services_context(self):
        response = self.client.get("/cl/es/servicios/otros-servicios/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "servicios_externos")

    def test_configuracion_route_uses_configuracion_context(self):
        response = self.client.get("/cl/es/configuracion/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_help_context(response), "configuracion")

    def test_documentos_context_uses_taller_api_alias(self):
        html = _html(self.client.get(reverse("chile:documentos:lista_documentos")))

        self.assertIn("function resolveApiHelpContext(context)", html)
        self.assertIn("context === 'documentos' ? 'taller' : context", html)
        self.assertIn("const apiContext = resolveApiHelpContext(context)", html)
        self.assertIn("api/faqs/${apiContext}/", html)
        self.assertIn("api/pasos/${apiContext}/", html)


class AyudaContextualAnonymousTests(TestCase):
    def test_anonymous_user_does_not_see_contextual_help_fab(self):
        response = self.client.get(reverse("chile:clientes:lista_clientes"))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('id="help-fab"', _html(response))


class AyudaContextualLocalizationTests(TestCase):
    def test_us_english_route_marks_help_language_as_english(self):
        empresa = EmpresaFactory(
            pais="US",
            moneda="USD",
            zona_horaria="America/New_York",
            with_config=True,
        )
        self.client.force_login(empresa.user)

        response = self.client.get(reverse("us_en:clientes:lista_clientes"))

        self.assertEqual(response.status_code, 200)
        html = _html(response)
        self.assertIn('data-help-language="en"', html)
        self.assertEqual(_help_context(response), "clientes")
