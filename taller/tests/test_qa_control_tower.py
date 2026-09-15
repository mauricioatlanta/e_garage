from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.urls import reverse

from taller.context_processors.business_modules import business_modules
from taller.context_processors.empresa_contexto import empresa_contexto
from taller.context_processors.feature_flags import country_features
from taller.middleware.empresa_resolver import EmpresaResolverMiddleware
from taller.qa_control.auth import is_control_tower_user
from taller.qa_control.context import (
    QA_SESSION_KEY,
    clear_qa_control_context,
    get_qa_control_context,
    is_qa_empresa,
    resolve_qa_empresa,
    set_qa_control_context,
    find_qa_empresas,
)
from taller.qa_control.views import control
from taller.qa_control.views import exit_control
from taller.services.empresa_service import get_empresa_safe
from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory, UserFactory


class QAAuthorizedUserTests(TestCase):
    def test_only_mauricio_with_superuser_is_authorized(self):
        mauricio = UserFactory(email="mauricioatlanta@gmail.com", is_superuser=True)
        mauricio_without_superuser = UserFactory(email="mauricioatlanta@gmail.com")
        other_superuser = UserFactory(email="other@example.com", is_superuser=True)
        staff = UserFactory(email="staff@example.com", is_staff=True)
        normal = UserFactory(email="normal@example.com")

        self.assertTrue(is_control_tower_user(mauricio))
        self.assertFalse(is_control_tower_user(mauricio_without_superuser))
        self.assertFalse(is_control_tower_user(other_superuser))
        self.assertFalse(is_control_tower_user(staff))
        self.assertFalse(is_control_tower_user(normal))

    def test_control_view_rejects_every_non_authorized_role(self):
        factory = RequestFactory()
        users = [
            UserFactory(email="mauricioatlanta@gmail.com"),
            UserFactory(email="other@example.com", is_superuser=True),
            UserFactory(email="staff@example.com", is_staff=True),
            UserFactory(email="normal@example.com"),
        ]
        for user in users:
            request = factory.get("/qa/control/")
            request.user = user
            with self.assertRaises(PermissionDenied):
                control(request)


class QAContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory(email="mauricioatlanta@gmail.com", is_superuser=True)
        self.owner_empresa = EmpresaFactory(user=self.user, nombre_taller="Empresa A", pais="CL")
        self.qa_empresa = EmpresaFactory(nombre_taller="Demo QA Desarme Norte", pais="CL")
        ConfiguracionEmpresaFactory(
            empresa=self.owner_empresa, rubro_principal="WORKSHOP", rubros=[]
        )
        ConfiguracionEmpresaFactory(
            empresa=self.qa_empresa, rubro_principal="DESARMADURIA", rubros=[]
        )
        self.qa_settings = override_settings(
            QA_CONTROL_TENANTS={("CL", "DESARMADURIA"): self.qa_empresa.pk}
        )
        self.qa_settings.enable()
        self.addCleanup(self.qa_settings.disable)

    def request(self, path="/cl/es/desarme/"):
        request = self.factory.get(path)
        request.user = self.user
        SessionMiddleware(lambda req: HttpResponse("ok")).process_request(request)
        MessageMiddleware(lambda req: HttpResponse("ok")).process_request(request)
        return request

    def test_control_url_and_selector_use_existing_qa_tenant(self):
        self.assertEqual(reverse("qa_control:control"), "/qa/control/")
        request = self.request("/qa/control/")
        response = control(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Torre de Control QA", response.content)

        request = self.factory.post(
            "/qa/control/",
            {"country": "CL", "rubro": "DESARMADURIA", "empresa_id": str(self.qa_empresa.pk)},
        )
        request.user = self.user
        SessionMiddleware(lambda req: HttpResponse("ok")).process_request(request)
        MessageMiddleware(lambda req: HttpResponse("ok")).process_request(request)
        response = control(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.session[QA_SESSION_KEY]["empresa_id"], self.qa_empresa.pk)

    def test_exit_view_removes_context_without_logging_out(self):
        request = self.request("/qa/control/exit/")
        self.assertTrue(set_qa_control_context(request, self.qa_empresa))
        request.method = "GET"
        response = exit_control(request)
        self.assertEqual(response.status_code, 405)

        request = self.factory.post("/qa/control/exit/")
        request.user = self.user
        SessionMiddleware(lambda req: HttpResponse("ok")).process_request(request)
        MessageMiddleware(lambda req: HttpResponse("ok")).process_request(request)
        set_qa_control_context(request, self.qa_empresa)
        response = exit_control(request)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(QA_SESSION_KEY, request.session)
        self.assertTrue(request.user.is_authenticated)

    def test_session_context_resolves_b_without_changing_owner_a(self):
        request = self.request()
        self.assertTrue(set_qa_control_context(request, self.qa_empresa))
        self.assertEqual(resolve_qa_empresa(request), self.qa_empresa)
        self.assertEqual(request.user.empresa, self.owner_empresa)

        middleware = EmpresaResolverMiddleware(lambda req: HttpResponse("ok"))
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.empresa, self.qa_empresa)
        self.assertEqual(request.company, self.qa_empresa)
        self.assertEqual(request.country, "CL")
        self.assertEqual(request.qa_control_context["empresa_id"], self.qa_empresa.pk)
        self.assertEqual(get_empresa_safe(request), self.qa_empresa)

        self.assertEqual(empresa_contexto(request)["empresa"], self.qa_empresa)
        self.assertEqual(get_empresa_safe(request), self.qa_empresa)
        self.assertIn("business_modules", business_modules(request))
        self.assertEqual(country_features(request)["country_code"], "CL")
        self.assertEqual(request.user.empresa, self.owner_empresa)

    def test_exit_clears_session_and_normal_resolution_returns_a(self):
        request = self.request()
        self.assertTrue(set_qa_control_context(request, self.qa_empresa))
        clear_qa_control_context(request)
        self.assertNotIn(QA_SESSION_KEY, request.session)

        middleware = EmpresaResolverMiddleware(lambda req: HttpResponse("ok"))
        middleware(request)
        self.assertEqual(request.empresa, self.owner_empresa)


    def test_tampered_country_rubro_or_company_is_rejected_and_cleared(self):
        request = self.request()
        request.session[QA_SESSION_KEY] = {
            "country": "US",
            "rubro": "WORKSHOP",
            "empresa_id": self.qa_empresa.pk,
            "user_id": self.user.pk,
        }
        self.assertIsNone(resolve_qa_empresa(request))
        self.assertNotIn(QA_SESSION_KEY, request.session)

        request.session[QA_SESSION_KEY] = {
            "country": "CL",
            "rubro": "DESARMADURIA",
            "empresa_id": 999999999,
            "user_id": self.user.pk,
        }
        self.assertIsNone(resolve_qa_empresa(request))
        self.assertNotIn(QA_SESSION_KEY, request.session)

    def test_session_context_cannot_be_reused_by_another_user(self):
        request = self.request()
        self.assertTrue(set_qa_control_context(request, self.qa_empresa))
        other = UserFactory(email="other@example.com", is_superuser=True)
        request.user = other
        self.assertIsNone(resolve_qa_empresa(request))
        self.assertNotIn(QA_SESSION_KEY, request.session)

    def test_non_qa_company_is_not_selectable(self):
        request = self.request()
        ordinary = EmpresaFactory(nombre_taller="Taller Real", pais="CL")
        ConfiguracionEmpresaFactory(empresa=ordinary, rubro_principal="WORKSHOP", rubros=[])
        self.assertFalse(set_qa_control_context(request, ordinary))
        self.assertIsNone(get_qa_control_context(request))

        named_demo = EmpresaFactory(nombre_taller="Demo Taller Coincidente", pais="CL")
        ConfiguracionEmpresaFactory(empresa=named_demo, rubro_principal="WORKSHOP", rubros=[])
        with override_settings(QA_CONTROL_TENANTS={}):
            self.assertFalse(set_qa_control_context(request, named_demo))

        self.qa_empresa.suscripcion_activa = False
        self.qa_empresa.save(update_fields=["suscripcion_activa"])
        self.assertFalse(set_qa_control_context(request, self.qa_empresa))

    def test_real_allauth_logout_flushes_qa_context(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[QA_SESSION_KEY] = {
            "country": "CL",
            "rubro": "DESARMADURIA",
            "empresa_id": self.qa_empresa.pk,
            "user_id": self.user.pk,
        }
        session.save()

        response = self.client.post(reverse("account_logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(QA_SESSION_KEY, self.client.session)
        self.assertNotIn("_auth_user_id", self.client.session)

        self.client.force_login(self.user)
        self.assertNotIn(QA_SESSION_KEY, self.client.session)
        request = self.request()
        EmpresaResolverMiddleware(lambda req: HttpResponse("ok"))(request)
        self.assertEqual(request.empresa, self.owner_empresa)


class QAAuditedMatrixTests(TestCase):
    """La matriz efectiva refleja únicamente los tenants QA auditados."""

    AUDITED_CL_MATRIX = {
        ("CL", "WORKSHOP"): 48,
        ("CL", "DESARMADURIA"): 49,
        ("CL", "PARTS"): 50,
        ("CL", "DETAILING"): 53,
        ("CL", "TIRE"): 54,
        ("CL", "EXHAUST"): 55,
        ("CL", "FLEET"): 56,
        ("CL", "MIXED"): 57,
    }

    def test_effective_matrix_contains_only_audited_chile_tenants(self):
        self.assertEqual(settings.QA_CONTROL_TENANTS, self.AUDITED_CL_MATRIX)
        self.assertNotIn(("US", "WORKSHOP"), settings.QA_CONTROL_TENANTS)
        self.assertNotIn(("US", "DESARMADURIA"), settings.QA_CONTROL_TENANTS)
        self.assertNotIn(("US", "PARTS"), settings.QA_CONTROL_TENANTS)
        self.assertNotIn(("US", "TIRE"), settings.QA_CONTROL_TENANTS)
        self.assertNotIn(51, settings.QA_CONTROL_TENANTS.values())
        self.assertNotIn(52, settings.QA_CONTROL_TENANTS.values())

    def test_each_matrix_entry_resolves_its_configured_tenant(self):
        tenants = {}
        for country, rubro in self.AUDITED_CL_MATRIX:
            empresa = EmpresaFactory(
                pais=country,
                suscripcion_activa=True,
                nombre_taller=f"QA {rubro}",
            )
            ConfiguracionEmpresaFactory(
                empresa=empresa,
                rubro_principal=rubro,
                rubros=[],
            )
            tenants[(country, rubro)] = empresa

        test_matrix = {key: empresa.pk for key, empresa in tenants.items()}
        with override_settings(QA_CONTROL_TENANTS=test_matrix):
            for (country, rubro), empresa in tenants.items():
                candidates = list(find_qa_empresas(country, rubro))
                self.assertEqual([item.pk for item in candidates], [empresa.pk])
                self.assertTrue(is_qa_empresa(empresa))

    def test_invalid_or_unallowlisted_matrix_entries_are_not_selectable(self):
        valid = EmpresaFactory(pais="CL", suscripcion_activa=True)
        ConfiguracionEmpresaFactory(empresa=valid, rubro_principal="WORKSHOP", rubros=[])
        wrong_country = EmpresaFactory(pais="US", suscripcion_activa=True)
        ConfiguracionEmpresaFactory(empresa=wrong_country, rubro_principal="WORKSHOP", rubros=[])
        wrong_rubro = EmpresaFactory(pais="CL", suscripcion_activa=True)
        ConfiguracionEmpresaFactory(empresa=wrong_rubro, rubro_principal="PARTS", rubros=[])
        inactive = EmpresaFactory(pais="CL", suscripcion_activa=False)
        ConfiguracionEmpresaFactory(empresa=inactive, rubro_principal="WORKSHOP", rubros=[])

        with override_settings(QA_CONTROL_TENANTS={("CL", "WORKSHOP"): valid.pk}):
            self.assertEqual(list(find_qa_empresas("CL", "WORKSHOP")), [valid])
            self.assertEqual(list(find_qa_empresas("US", "WORKSHOP")), [])
            self.assertEqual(list(find_qa_empresas("CL", "PARTS")), [])
            self.assertFalse(is_qa_empresa(wrong_country))
            self.assertFalse(is_qa_empresa(wrong_rubro))
            self.assertFalse(is_qa_empresa(inactive))
            self.assertEqual(list(find_qa_empresas("CL", "MIXED")), [])
