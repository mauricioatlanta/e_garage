from types import SimpleNamespace

from django.test import SimpleTestCase

from taller.servicios.catalog_bootstrap import get_master_catalog_service_items
from taller.servicios.views import _active_service_rubros


class CarWashServiceCatalogTests(SimpleTestCase):
    def test_carwash_fallback_does_not_expose_workshop_catalog(self):
        items = get_master_catalog_service_items("CL", rubros={"DETAILING"}, limit=50)
        labels = " ".join(item["nombre"].lower() for item in items)

        self.assertTrue(items)
        self.assertIn("lavado", labels)
        self.assertNotIn("aceite", labels)
        self.assertNotIn("motor", labels)
        self.assertNotIn("freno", labels)

    def test_workshop_fallback_keeps_existing_catalog(self):
        items = get_master_catalog_service_items("CL", rubros={"WORKSHOP"}, limit=50)
        labels = " ".join(item["nombre"].lower() for item in items)

        self.assertIn("aceite", labels)
        self.assertIn("motor", labels)

    def test_support_mode_overrides_company_rubro_for_catalog_scope(self):
        empresa = SimpleNamespace(
            config=SimpleNamespace(
                get_effective_rubros=lambda: ["WORKSHOP"],
                rubro_principal="WORKSHOP",
            )
        )
        request = SimpleNamespace(
            user=SimpleNamespace(is_superuser=True),
            session={"modo_soporte_rubros": ["detailing"]},
        )

        self.assertEqual(_active_service_rubros(empresa, request), {"DETAILING"})
