from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE
from taller.models.vehiculos import Vehiculo
from taller.models.vehiculo_financial import VehicleFinancialEvent
from taller.models.snapshot_queue import SnapshotQueueItem
from taller.services.financial_event_service import FinancialEventService
from taller.services.snapshot_queue import SnapshotQueue


class FinancialEventServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_finance", password="testpass")
        self.empresa = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=self.user)
        self.cliente = Cliente.objects.create(empresa=self.empresa, nombre="Cliente Test")
        self.vehiculo = Vehiculo.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo_uso=Vehiculo.TIPO_USO_DESARME,
            marca_texto="BMW",
            modelo_texto="320i",
            patente="TEST123",
            anio=2018,
            vin="VINTEST123",
            fecha_ingreso_desarme="2025-01-01",
            estado_desarme="INGRESADO",
        )

    def test_create_purchase_event_is_idempotent(self):
        event1 = FinancialEventService.create_purchase_event(
            self.vehiculo,
            self.empresa,
            "1500000",
            "Compra de vehículo de desarme demo",
        )
        event2 = FinancialEventService.create_purchase_event(
            self.vehiculo,
            self.empresa,
            "1500000",
            "Compra de vehículo de desarme demo",
        )

        self.assertEqual(event1.id, event2.id)
        self.assertEqual(VehicleFinancialEvent.objects.filter(event_type=VehicleFinancialEvent.EVENT_TYPE_COMPRA).count(), 1)
        self.assertIsNotNone(event1.event_hash)
        self.assertEqual(event1.event_version, 1)

    def test_create_cost_event_is_idempotent(self):
        event1 = FinancialEventService.create_cost_event(
            self.vehiculo,
            self.empresa,
            "200000",
            "Costo transporte/grúa demo",
        )
        event2 = FinancialEventService.create_cost_event(
            self.vehiculo,
            self.empresa,
            "200000",
            "Costo transporte/grúa demo",
        )

        self.assertEqual(event1.id, event2.id)
        self.assertEqual(VehicleFinancialEvent.objects.filter(event_type=VehicleFinancialEvent.EVENT_TYPE_COSTO).count(), 1)
        self.assertIsNotNone(event1.event_hash)
        self.assertEqual(event1.event_version, 1)

    def test_sync_event_from_linea_repuesto_is_idempotent(self):
        pieza = PiezaDesarme.objects.create(
            empresa=self.empresa,
            vehiculo=self.vehiculo,
            codigo="ENG-BMW-01",
            nombre="Motor BMW 320i",
            cantidad=1,
            costo_asignado="500000",
            precio_sugerido="1200000",
            fecha_extraccion="2025-01-01",
            activo=True,
            estado_pieza=ESTADO_DISPONIBLE,
        )

        documento = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="PTS",
            estado="EMITIDO",
            fecha_emision="2025-01-02",
            vehiculo=self.vehiculo,
            moneda="CLP",
            country="CL",
        )

        linea = LineaRepuesto.objects.create(
            documento=documento,
            codigo=pieza.codigo,
            nombre=pieza.nombre,
            cantidad=1,
            precio_unitario="1200000",
            descuento="0",
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=pieza,
            costo_linea="500000",
        )

        event1 = FinancialEventService.sync_event_from_linea_repuesto(linea)
        event2 = FinancialEventService.sync_event_from_linea_repuesto(linea)

        self.assertEqual(event1.id, event2.id)
        self.assertEqual(VehicleFinancialEvent.objects.filter(event_type=VehicleFinancialEvent.EVENT_TYPE_VENTA).count(), 1)
        self.assertEqual(event1.event_version, 1)
        self.assertIsNotNone(event1.event_hash)

    def test_bulk_create_lineas_repuesto_bypasses_post_save_and_requires_manual_snapshot_enqueue(self):
        documento = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="PTS",
            estado="BORRADOR",
            fecha_emision="2025-01-02",
            vehiculo=self.vehiculo,
            moneda="CLP",
            country="CL",
        )

        lineas = [
            LineaRepuesto(
                documento=documento,
                codigo=f"REP-{i}",
                nombre=f"Repuesto {i}",
                cantidad=1,
                precio_unitario=10000,
                descuento=0,
                origen_repuesto=ORIGEN_DESARME,
            )
            for i in range(2)
        ]
        LineaRepuesto.objects.bulk_create(lineas)

        self.assertFalse(SnapshotQueueItem.objects.filter(documento=documento).exists())

        SnapshotQueue.enqueue_for_document(documento)
        self.assertTrue(SnapshotQueueItem.objects.filter(documento=documento).exists())

    def test_event_hash_unique_constraint_allows_nulls_but_blocks_duplicates(self):
        event1 = VehicleFinancialEvent.objects.create(
            vehiculo=self.vehiculo,
            empresa=self.empresa,
            tipo=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            event_type=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            monto="10000",
            descripcion="Compra demo",
        )
        event2 = VehicleFinancialEvent.objects.create(
            vehiculo=self.vehiculo,
            empresa=self.empresa,
            tipo=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            event_type=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            monto="10000",
            descripcion="Compra demo",
        )
        self.assertIsNone(event1.event_hash)
        self.assertIsNone(event2.event_hash)
        self.assertNotEqual(event1.id, event2.id)

        event1.event_hash = "FIN_EVENT_V1|COMPRA|1|1|10000|Compra demo"
        event1.save(update_fields=["event_hash"])
        with self.assertRaises(IntegrityError):
            VehicleFinancialEvent.objects.create(
                vehiculo=self.vehiculo,
                empresa=self.empresa,
                tipo=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
                event_type=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
                monto="10000",
                descripcion="Compra demo",
                event_hash=event1.event_hash,
            )

    def test_rebuild_financial_events_command_fixes_missing_hashes_and_queues_snapshot(self):
        pieza = PiezaDesarme.objects.create(
            empresa=self.empresa,
            vehiculo=self.vehiculo,
            codigo="ENG-BMW-02",
            nombre="Motor BMW 320i",
            cantidad=1,
            costo_asignado="500000",
            precio_sugerido="1200000",
            fecha_extraccion="2025-01-01",
            activo=True,
            estado_pieza=ESTADO_DISPONIBLE,
        )

        documento = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="PTS",
            estado="EMITIDO",
            fecha_emision="2025-01-02",
            vehiculo=self.vehiculo,
            moneda="CLP",
            country="CL",
        )
        SnapshotQueueItem.objects.filter(documento=documento).delete()

        linea = LineaRepuesto.objects.create(
            documento=documento,
            codigo=pieza.codigo,
            nombre=pieza.nombre,
            cantidad=1,
            precio_unitario="1200000",
            descuento="0",
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=pieza,
        )

        venta_event = VehicleFinancialEvent.objects.create(
            vehiculo=self.vehiculo,
            empresa=self.empresa,
            tipo=VehicleFinancialEvent.EVENT_TYPE_VENTA,
            event_type=VehicleFinancialEvent.EVENT_TYPE_VENTA,
            monto="1200000",
            descripcion="Venta de pieza demo",
            linea_repuesto=linea,
        )
        compra_event = VehicleFinancialEvent.objects.create(
            vehiculo=self.vehiculo,
            empresa=self.empresa,
            tipo=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            event_type=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            monto="1500000",
            descripcion="Compra de vehículo demo",
        )

        call_command("rebuild_financial_events", "--fix")

        venta_event.refresh_from_db()
        compra_event.refresh_from_db()
        self.assertIsNotNone(venta_event.event_hash)
        self.assertIsNotNone(compra_event.event_hash)
        self.assertTrue(SnapshotQueueItem.objects.filter(documento=documento).exists())
