from django.test import TestCase

from taller.constants.product_profiles import PRODUCT_TIRE, RUBRO_TO_PRODUCT
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.repuesto import Repuesto
from taller.services.registration_service import RegistrationService
from taller.services.workspace_service import WorkspaceService
from taller.tests.factories import EmpresaFactory, RepuestoFactory, UserFactory


class TireWorkspaceTests(TestCase):
    def test_tire_part_has_structured_measure_and_search(self):
        empresa = EmpresaFactory()
        tire = RepuestoFactory(
            empresa=empresa,
            nombre="Michelin Energy XM2",
            part_number="MIC-2055516",
            ancho=205,
            perfil=55,
            aro=16,
            indice_carga="91",
            codigo_velocidad="V",
            marca_neumatico="Michelin",
            modelo_neumatico="Energy XM2",
        )
        RepuestoFactory(empresa=empresa, nombre="Pastilla freno", part_number="D1184")

        results = list(Repuesto.objects.filter(empresa=empresa).buscar_medida_neumatico("205/55R16"))

        self.assertEqual(tire.medida_completa, "205/55R16")
        self.assertEqual(results, [tire])

    def test_tire_rubro_resolves_independent_product_and_workspace(self):
        self.assertEqual(RUBRO_TO_PRODUCT["TIRE"], PRODUCT_TIRE)

        empresa = EmpresaFactory()
        config = ConfiguracionEmpresa.objects.create(
            empresa=empresa,
            nombre_publico=empresa.nombre_taller,
            rubro_principal="TIRE",
            rubros=["TIRE"],
        )

        workspace = WorkspaceService.resolve(config, url_prefix="/cl/es")

        self.assertEqual(workspace["product_key"], PRODUCT_TIRE)
        self.assertEqual(workspace["brand"]["product_name"], "eGarage Neumáticos & Vulcanización")
        self.assertTrue(any(item["url"].endswith("/repuestos/pos/") for item in workspace["nav"]))

    def test_registration_service_accepts_direct_tire_rubro(self):
        user = UserFactory(email="tire-owner@example.com", username="tire-owner")

        result = RegistrationService.create_company_for_user(
            user=user,
            company_data={
                "nombre_taller": "Llantera Alameda",
                "pais": "CL",
                "rubro_principal": "TIRE",
            },
            plan_type="trial",
        )

        config = result["empresa"].config
        self.assertEqual(config.rubro_principal, "TIRE")
        self.assertEqual(WorkspaceService.get_workspace_def(config).product_key, PRODUCT_TIRE)
