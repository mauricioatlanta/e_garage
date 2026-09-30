import json
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_STOCK_BODEGA
from taller.repuestos.pos_service import PartsPOSService
from taller.tests.factories import EmpresaFactory, RepuestoFactory


class PartsPOSTests(TestCase):
    def setUp(self):
        self.empresa = EmpresaFactory()
        Group.objects.get_or_create(name="Owner")[0].user_set.add(self.empresa.user)
        self.client.force_login(self.empresa.user)

    def test_pos_search_finds_oem_equivalent_name_and_tire_measure(self):
        tire = RepuestoFactory(
            empresa=self.empresa,
            nombre="Continental PremiumContact",
            part_number="CON-2055516",
            codigo_oem="OEM-TIRE-205",
            codigos_equivalentes="ALT-205 FMSI-205",
            cantidad_stock=4,
            ubicacion="Pasillo 2 Estante B",
            ancho=205,
            perfil=55,
            aro=16,
        )

        by_measure = list(PartsPOSService.search(self.empresa, "205/55R16"))
        by_equivalent = list(PartsPOSService.search(self.empresa, "FMSI-205"))

        self.assertEqual(by_measure, [tire])
        self.assertEqual(by_equivalent, [tire])

    def test_pos_confirm_sale_creates_pts_and_discounts_stock_atomically(self):
        repuesto = RepuestoFactory(
            empresa=self.empresa,
            nombre="Pastilla Freno Delantera",
            part_number="D1184",
            precio_compra=Decimal("10000.00"),
            precio_venta=Decimal("25000.00"),
            cantidad_stock=5,
            ubicacion="A2-B4",
        )

        response = self.client.post(
            "/cl/es/repuestos/pos/confirmar/",
            data=json.dumps({
                "payment_method": "tarjeta",
                "items": [{"repuesto_id": repuesto.pk, "cantidad": 2}],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])

        repuesto.refresh_from_db()
        self.assertEqual(repuesto.cantidad_stock, 3)

        documento = Documento.objects.get(pk=data["documento_id"])
        self.assertEqual(documento.tipo, "PTS")
        self.assertEqual(documento.estado, "EMITIDO")
        self.assertEqual(documento.metodo_pago, "tarjeta")
        self.assertTrue(documento.pagado)
        self.assertEqual(documento.lineas_repuesto.count(), 1)

        linea = LineaRepuesto.objects.get(documento=documento)
        self.assertEqual(linea.origen_repuesto, ORIGEN_STOCK_BODEGA)
        self.assertEqual(linea.cantidad, 2)

    def test_pos_rolls_back_when_stock_is_insufficient(self):
        repuesto = RepuestoFactory(
            empresa=self.empresa,
            nombre="Filtro Aceite",
            part_number="FIL-001",
            precio_venta=Decimal("9000.00"),
            cantidad_stock=1,
        )

        response = self.client.post(
            "/cl/es/repuestos/pos/confirmar/",
            data=json.dumps({
                "payment_method": "efectivo",
                "items": [{"repuesto_id": repuesto.pk, "cantidad": 2}],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.cantidad_stock, 1)
        self.assertFalse(Documento.objects.filter(tipo="PTS").exists())
