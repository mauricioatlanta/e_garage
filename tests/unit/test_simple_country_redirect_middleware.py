"""
Tests para SimpleCountryRedirectMiddleware.
Cubre: solo GET/HEAD, request.empresa activa, idioma en URL, forzar idioma cuando falta.
"""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

from taller.middleware.simple_country_redirect import SimpleCountryRedirectMiddleware
from taller.models.empresa import Empresa

User = get_user_model()


@override_settings(
    EGARAGE_ACTIVE_COUNTRIES=("CL", "US"),
    EGARAGE_COUNTRY_DEFAULT_LANG={"US": "en", "CL": "es"},
)
class SimpleCountryRedirectMiddlewareTest(TestCase):
    """Tests de redirección por país/idioma según empresa activa."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SimpleCountryRedirectMiddleware(lambda r: None)

    def _request(self, path, method="GET", user=None, empresa=None, query_string=""):
        if method == "GET":
            request = self.factory.get(path)
        else:
            request = self.factory.generic(method, path)
        if query_string:
            request.META["QUERY_STRING"] = query_string
        request.user = user or type("User", (), {"is_authenticated": False})()
        if empresa is not None:
            request.empresa = empresa
        return request

    def test_post_no_redirect(self):
        """CRÍTICO: POST no debe redirigir (evita perder body/CSRF)."""
        user = User.objects.create_user(username="u1", password="pw")
        emp = Empresa.objects.create(nombre_taller="T", pais="US", user=user)
        request = self._request("/cl/es/documentos/form/", method="POST", user=user, empresa=emp)
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIsNone(response)

    def test_empresa_us_cl_es_redirects_to_us_en(self):
        """A. Empresa US: /cl/es/documentos/form/ -> /us/en/documentos/form/"""
        user = User.objects.create_user(username="u_us", password="pw")
        emp = Empresa.objects.create(nombre_taller="US Garage", pais="US", user=user)
        request = self._request("/cl/es/documentos/form/", user=user, empresa=emp)
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/us/en/documentos/form")

    def test_empresa_us_us_es_redirects_to_us_en(self):
        """A. Empresa US: /us/es/documentos/form/ -> /us/en/documentos/form/"""
        user = User.objects.create_user(username="u_us2", password="pw")
        emp = Empresa.objects.create(nombre_taller="US Garage 2", pais="US", user=user)
        request = self._request("/us/es/documentos/form/", user=user, empresa=emp)
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/us/en/documentos/form")

    def test_empresa_us_no_lang_redirects_to_us_en(self):
        """A. Empresa US: /us/documentos/form/ -> /us/en/documentos/form/ (forzar idioma)."""
        user = User.objects.create_user(username="u_us3", password="pw")
        emp = Empresa.objects.create(nombre_taller="US Garage 3", pais="US", user=user)
        request = self._request("/us/documentos/form/", user=user, empresa=emp)
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/us/en/documentos/form")

    def test_empresa_cl_us_en_redirects_to_cl_es(self):
        """B. Empresa CL: /us/en/documentos/form/ -> /cl/es/documentos/form/"""
        user = User.objects.create_user(username="u_cl", password="pw")
        emp = Empresa.objects.create(nombre_taller="CL Garage", pais="CL", user=user)
        request = self._request("/us/en/documentos/form/", user=user, empresa=emp)
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/cl/es/documentos/form")

    def test_preserves_query_string(self):
        """Query string se preserva en la redirección."""
        user = User.objects.create_user(username="u_qs", password="pw")
        emp = Empresa.objects.create(nombre_taller="US QS", pais="US", user=user)
        request = self._request(
            "/cl/es/documentos/form/", user=user, empresa=emp, query_string="tipo=factura"
        )
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIn("?", response.url)
        self.assertIn("tipo=factura", response.url, "Query string debe preservarse")
        self.assertEqual(response.url.split("?")[0], "/us/en/documentos/form")

    def test_uses_request_empresa_when_set(self):
        """Usa request.empresa (empresa activa) cuando está definida."""
        user = User.objects.create_user(username="u_req_emp", password="pw")
        emp = Empresa.objects.create(nombre_taller="CL Req", pais="CL", user=user)
        request = self._request("/us/en/documentos/form/", user=user, empresa=emp)
        request.user.empresa = emp  # también en user por si acaso
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.url, "/cl/es/documentos/form")

    def test_no_redirect_when_country_and_lang_match(self):
        """No redirige si país e idioma ya son correctos."""
        user = User.objects.create_user(username="u_ok", password="pw")
        emp = Empresa.objects.create(nombre_taller="CL Ok", pais="CL", user=user)
        request = self._request("/cl/es/documentos/form/", user=user, empresa=emp)
        request.user.empresa = emp
        response = self.middleware.process_request(request)
        self.assertIsNone(response)
