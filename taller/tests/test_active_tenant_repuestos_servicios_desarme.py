import json
from unittest.mock import patch

from django.http import Http404
from django.test import RequestFactory, TestCase

from taller.models.repuesto import Repuesto
from taller.models.venta_desarme import VentaDesarme
from taller.repuestos.views_cbv import RepuestoDetailView, RepuestoListView
from taller.servicios.models import CategoriaServicio, Servicio
from taller.servicios.views import buscar_servicios_api
from taller.servicios.api_servicios_moderno import api_buscar_servicios
from taller.desarme.views_venta import recibo_venta
from taller.tests.factories import EmpresaFactory, PiezaDesarmeFactory


class ActiveTenantRepuestosServiciosDesarmeTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a = EmpresaFactory(nombre_taller="Empresa A")
        self.empresa_b = EmpresaFactory(nombre_taller="Empresa B")
        self.user = self.empresa_a.user

    def request(self, path="/cl/es/taller/"):
        request = self.factory.get(path)
        request.user = self.user
        request.empresa = self.empresa_b
        return request

    def test_repuestos_list_and_detail_are_scoped_to_active_tenant(self):
        repuesto_a = Repuesto.objects.create(
            empresa=self.empresa_a, part_number="A-001", nombre="Repuesto A"
        )
        repuesto_b = Repuesto.objects.create(
            empresa=self.empresa_b, part_number="B-001", nombre="Repuesto B"
        )

        list_view = RepuestoListView()
        list_view.request = self.request()
        self.assertEqual(list(list_view.get_queryset()), [repuesto_b])

        detail_view = RepuestoDetailView()
        detail_view.request = self.request()
        detail_view.kwargs = {"pk": repuesto_b.pk}
        self.assertEqual(detail_view.get_object(), repuesto_b)

        detail_view.kwargs = {"pk": repuesto_a.pk}
        with self.assertRaises(Http404):
            detail_view.get_object()

    def test_service_apis_use_active_tenant_and_exclude_owner_tenant(self):
        categoria = CategoriaServicio.objects.create(country="CL", code="MOTOR")
        servicio_a = Servicio.objects.create(
            empresa=self.empresa_a, categoria=categoria, nombre="Servicio A"
        )
        servicio_b = Servicio.objects.create(
            empresa=self.empresa_b, categoria=categoria, nombre="Servicio B"
        )

        response = buscar_servicios_api(self.request())
        names = {item["nombre"] for item in json.loads(response.content)["servicios"]}
        self.assertIn(servicio_b.nombre, names)
        self.assertNotIn(servicio_a.nombre, names)

        response = api_buscar_servicios(self.request("/cl/es/api/servicios/"))
        names = {item["nombre"] for item in json.loads(response.content)["servicios"]}
        self.assertIn(servicio_b.nombre, names)
        self.assertNotIn(servicio_a.nombre, names)

    def test_desarme_sale_receipt_uses_active_tenant(self):
        venta_a = VentaDesarme.objects.create(empresa=self.empresa_a, cliente_nombre="Cliente A")
        venta_b = VentaDesarme.objects.create(empresa=self.empresa_b, cliente_nombre="Cliente B")

        with patch("taller.desarme.views_venta.render", return_value="rendered"):
            response = recibo_venta(self.request(), venta_b.pk)
        self.assertEqual(response, "rendered")

        with self.assertRaises(Http404):
            recibo_venta(self.request(), venta_a.pk)

    def test_desarme_piece_factory_keeps_each_tenant_isolated(self):
        pieza_a = PiezaDesarmeFactory(empresa=self.empresa_a)
        pieza_b = PiezaDesarmeFactory(empresa=self.empresa_b)
        self.assertEqual(pieza_a.empresa_id, self.empresa_a.id)
        self.assertEqual(pieza_b.empresa_id, self.empresa_b.id)
