from django.test import SimpleTestCase

from taller.servicios.catalog_bootstrap import get_master_catalog_service_items


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
