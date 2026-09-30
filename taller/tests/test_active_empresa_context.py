from django.test import RequestFactory, TestCase

from gestion_taller.urls import (
    country_aware_clientes_redirect,
    country_aware_workspace_redirect,
    redirect_to_home,
)
from taller.config.feature_flags import get_country_features
from taller.constants.business_modules import MOD_DESARME, MOD_REPUESTOS, MOD_SERVICIOS, MOD_VEHICULOS
from taller.context_processors.business_modules import business_modules
from taller.context_processors.empresa_contexto import empresa_contexto
from taller.context_processors.feature_flags import country_features
from taller.services.empresa_service import get_empresa_safe
from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory


class ActiveEmpresaContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, path, user, active_empresa=None):
        request = self.factory.get(path)
        request.user = user
        if active_empresa is not None:
            request.empresa = active_empresa
            request.company = active_empresa
            request.country = active_empresa.pais
        return request

    def test_normal_user_keeps_current_navigation_country_rubro_and_flags(self):
        empresa = EmpresaFactory(nombre_taller="Empresa Normal", pais="CL")
        ConfiguracionEmpresaFactory(
            empresa=empresa,
            rubro_principal="PARTS",
            rubros=[],
        )
        request = self._request("/cl/es/repuestos/", empresa.user, active_empresa=empresa)

        self.assertEqual(get_empresa_safe(request), empresa)

        empresa_ctx = empresa_contexto(request)
        self.assertEqual(empresa_ctx["empresa"], empresa)
        self.assertEqual(empresa_ctx["nombre_taller"], "Empresa Normal")

        modules_ctx = business_modules(request)
        self.assertIn(MOD_REPUESTOS, modules_ctx["business_modules"])
        self.assertNotIn(MOD_VEHICULOS, modules_ctx["business_modules"])
        self.assertNotIn(MOD_SERVICIOS, modules_ctx["business_modules"])

        flags_ctx = country_features(request)
        self.assertEqual(flags_ctx["country_code"], "CL")
        self.assertEqual(flags_ctx["country_features"], get_country_features("CL"))

        self.assertEqual(redirect_to_home(request)["Location"], "/cl/")
        self.assertEqual(country_aware_clientes_redirect(request)["Location"], "/cl/es/clientes/")
        self.assertEqual(
            country_aware_workspace_redirect(request, "buscar")["Location"],
            "/cl/es/workspace/buscar/",
        )

    def test_active_tenant_can_differ_from_user_owned_empresa(self):
        empresa_a = EmpresaFactory(nombre_taller="Empresa A Propietaria", pais="CL")
        ConfiguracionEmpresaFactory(
            empresa=empresa_a,
            rubro_principal="PARTS",
            rubros=[],
        )

        empresa_b = EmpresaFactory(nombre_taller="Empresa B QA", pais="US")
        ConfiguracionEmpresaFactory(
            empresa=empresa_b,
            rubro_principal="DESARMADURIA",
            rubros=[],
        )

        request = self._request("/us/en/desarme/", empresa_a.user, active_empresa=empresa_b)

        self.assertEqual(empresa_a.user.empresa, empresa_a)
        self.assertEqual(request.empresa, empresa_b)
        self.assertEqual(get_empresa_safe(request), empresa_b)

        empresa_ctx = empresa_contexto(request)
        self.assertEqual(empresa_ctx["empresa"], empresa_b)
        self.assertEqual(empresa_ctx["nombre_taller"], "Empresa B QA")

        modules_ctx = business_modules(request)
        self.assertIn(MOD_DESARME, modules_ctx["business_modules"])
        self.assertIn(MOD_REPUESTOS, modules_ctx["business_modules"])
        self.assertNotIn(MOD_VEHICULOS, modules_ctx["business_modules"])
        self.assertNotIn(MOD_SERVICIOS, modules_ctx["business_modules"])

        flags_ctx = country_features(request)
        self.assertEqual(flags_ctx["country_code"], "US")
        self.assertEqual(flags_ctx["country_features"], get_country_features("US"))

        self.assertEqual(redirect_to_home(request)["Location"], "/us/")
        self.assertEqual(country_aware_clientes_redirect(request)["Location"], "/us/clientes/")
        self.assertEqual(
            country_aware_workspace_redirect(request, "buscar")["Location"],
            "/us/en/workspace/buscar/",
        )

        self.assertEqual(empresa_a.user.empresa, empresa_a)
