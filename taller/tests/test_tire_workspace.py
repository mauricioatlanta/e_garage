from django.test import TestCase

from taller.constants.product_profiles import PRODUCT_TIRE, RUBRO_TO_PRODUCT
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.tire import Tire
from taller.services.registration_service import RegistrationService
from taller.services.workspace_service import WorkspaceService
from taller.tests.factories import EmpresaFactory, UserFactory

class TireWorkspaceTests(TestCase):
    def test_tire_part_has_structured_measure_and_search(self):
        empresa = EmpresaFactory()
        tire = Tire.objects.create(
            empresa=empresa,
            marca="Michelin",
            modelo="Energy XM2",
            ancho=205,
            perfil=55,
            aro=16,
            proveedor="Top",
            precio_compra=50,
            precio_venta=80,
            cantidad_stock=4,
            tipo="Nuevo",
        )
        Tire.objects.create(
            empresa=empresa,
            marca="Goodyear",
            modelo="EfficientGrip",
            ancho=175,
            perfil=70,
            aro=14,
            proveedor="Top",
            precio_compra=30,
            precio_venta=50,
            cantidad_stock=2,
            tipo="Nuevo",
        )

        results = list(Tire.objects.filter(empresa=empresa, ancho=205, perfil=55, aro=16))

        # medida_completa si existe en Tire, si no, construye la medida
        medida = getattr(tire, "medida_completa", f"{tire.ancho}/{tire.perfil} R{tire.aro}")
        self.assertEqual(medida, "205/55 R16")
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
        nav = {item["nav_key"]: item for item in workspace["nav"]}
        self.assertEqual(nav["tire_inventory"]["label"], "Neumáticos")
        self.assertEqual(nav["tire_services"]["label"], "Servicios Express")
        # Vulcanizacion oficial: 9 botones (incluye Kiosko Mio + Kiosko Global), sin Servicios extras, sin Vehiculos
        self.assertNotIn("tire_extra_services", nav)
        self.assertNotIn("tire_vehicles", nav)
        self.assertEqual(len(nav), 9)
        self.assertEqual(nav["tire_pos"]["label"], "Ventas")
        self.assertTrue(nav["tire_pos"]["url"].endswith("/repuestos/pos/"))
        # Fix vulcanizacion: Reportes ya NO va a reportes/ generico, va a tires/reportes/
        self.assertEqual(nav["tire_reports"]["url"], "/cl/es/tires/reportes/")

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
