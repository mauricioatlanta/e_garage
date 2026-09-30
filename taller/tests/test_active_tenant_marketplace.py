import json

from django.test import RequestFactory, TestCase

from marketplace.models import CasaRepuestos, ProductoCatalogo
from marketplace.views import api_buscar_precios_por_partnumber, api_producto_por_id
from taller.tests.factories import EmpresaFactory


class ActiveTenantMarketplaceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a = EmpresaFactory(nombre_taller="Empresa A")
        self.empresa_b = EmpresaFactory(nombre_taller="Empresa B")
        self.user = self.empresa_a.user

        self.casa_a = CasaRepuestos.objects.create(empresa=self.empresa_a, nombre="Casa A")
        self.casa_b = CasaRepuestos.objects.create(empresa=self.empresa_b, nombre="Casa B")
        self.producto_a = ProductoCatalogo.objects.create(
            empresa=self.empresa_a,
            casa_repuestos=self.casa_a,
            part_number="ABC-123",
            nombre="Producto A",
            precio_referencia=100,
        )
        self.producto_b = ProductoCatalogo.objects.create(
            empresa=self.empresa_b,
            casa_repuestos=self.casa_b,
            part_number="ABC123",
            nombre="Producto B",
            precio_referencia=200,
        )

    def request(self, path="/cl/es/marketplace/api/precios/"):
        request = self.factory.get(path, {"part_number": "ABC-123"})
        request.user = self.user
        request.empresa = self.empresa_b
        return request

    def test_price_lookup_uses_active_tenant_and_excludes_owner_data(self):
        response = api_buscar_precios_por_partnumber(self.request())
        payload = json.loads(response.content)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["precios"][0]["casa_repuestos"], "Casa B")

    def test_product_detail_uses_active_tenant_and_blocks_owner_product(self):
        response = api_producto_por_id(self.request(), self.producto_b.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["nombre"], "Producto B")

        response = api_producto_por_id(self.request(), self.producto_a.pk)
        self.assertEqual(response.status_code, 404)
