from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.pieza_desarme import (
    PiezaDesarme,
    ESTADO_DISPONIBLE,
)
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.services.financial_event_service import FinancialEventService
from taller.services.snapshot_generator_service import SnapshotGeneratorService


class Command(BaseCommand):
    help = "Crea una demo de desarme real con vehículo, piezas, documento PTS y línea de desarme."

    def add_arguments(self, parser):
        parser.add_argument("empresa_id", type=int, help="ID de la empresa destino")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Elimina el demo anterior de la empresa antes de crear datos nuevos.",
        )

    def handle(self, *args, **options):
        empresa = Empresa.objects.get(id=options["empresa_id"])
        if options["force"]:
            self._cleanup_demo(empresa)

        cliente = Cliente.objects.filter(empresa=empresa).first()
        if not cliente:
            cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Demo Desarme")

        fecha_ingreso = timezone.now().date() - timedelta(days=120)

        vehiculo = Vehiculo.objects.create(
            empresa=empresa,
            cliente=cliente,
            tipo_uso=Vehiculo.TIPO_USO_DESARME,
            marca_texto="BMW",
            modelo_texto="320i",
            patente="BMW320",
            anio=2018,
            vin="WBA8E1G50JNU00001",
            color=None,
            fecha_ingreso_desarme=fecha_ingreso,
            estado_desarme="INGRESADO",
            observaciones_desarme="Vehículo demo append-only event sourcing",
        )

        VehiculoDesarme.objects.create(
            empresa=empresa,
            vehiculo_origen_id=vehiculo.id,
            marca_texto="BMW",
            modelo_texto="320i",
            patente="BMW320",
            fecha_ingreso_desarme=fecha_ingreso,
            estado_desarme="INGRESADO",
        )

        piezas = [
            {
                "codigo": "ENG-BMW-01",
                "nombre": "Motor BMW 320i",
                "cantidad": 1,
                "costo_asignado": Decimal("500000"),
                "precio_sugerido": Decimal("1200000"),
            },
            {
                "codigo": "TRS-BMW-01",
                "nombre": "Caja BMW 320i",
                "cantidad": 1,
                "costo_asignado": Decimal("200000"),
                "precio_sugerido": Decimal("500000"),
            },
            {
                "codigo": "DOOR-BMW-01",
                "nombre": "Puerta BMW",
                "cantidad": 2,
                "costo_asignado": Decimal("50000"),
                "precio_sugerido": Decimal("150000"),
            },
        ]

        piezas_objs = []
        for data in piezas:
            pieza = PiezaDesarme.objects.create(
                empresa=empresa,
                vehiculo=vehiculo,
                codigo=data["codigo"],
                nombre=data["nombre"],
                cantidad=data["cantidad"],
                costo_asignado=data["costo_asignado"],
                precio_sugerido=data["precio_sugerido"],
                fecha_extraccion=timezone.now().date() - timedelta(days=90),
                activo=True,
                estado_pieza=ESTADO_DISPONIBLE,
            )
            piezas_objs.append(pieza)

        documento = Documento.objects.create(
            empresa=empresa,
            cliente=cliente,
            tipo="PTS",
            estado="BORRADOR",
            fecha_emision=timezone.now().date() - timedelta(days=30),
            vehiculo=vehiculo,
            moneda="CLP",
            country=getattr(empresa, "pais", "CL"),
            observaciones="Documento PTS demo creado por seed_desarme_demo",
        )

        for pieza in piezas_objs[:2]:
            LineaRepuesto.objects.create(
                documento=documento,
                codigo=pieza.codigo,
                nombre=pieza.nombre,
                cantidad=1,
                precio_unitario=pieza.precio_sugerido or pieza.costo_asignado,
                descuento=Decimal("0.00"),
                origen_repuesto=ORIGEN_DESARME,
                pieza_desarme=pieza,
                costo_linea=pieza.costo_asignado,
            )

        documento.recalcular_totales(save=True)
        documento.estado = "EMITIDO"
        documento.save(update_fields=["estado"])

        # IMPORTANTE:
        # El documento inicialmente fue BORRADOR.
        # Debemos sincronizar eventos financieros manualmente
        # para disparar el append-only event sourcing.
        FinancialEventService.sync_events_for_documento(documento)

        FinancialEventService.create_purchase_event(
            vehiculo,
            empresa,
            Decimal("1500000"),
            "Compra de vehículo de desarme demo",
        )
        FinancialEventService.create_cost_event(
            vehiculo,
            empresa,
            Decimal("200000"),
            "Costo transporte/grúa demo",
        )

        SnapshotGeneratorService.generate_snapshot_for_vehicle(vehiculo)

        self.stdout.write(self.style.SUCCESS("✅ Seed de desarme creada correctamente."))
        self.stdout.write(self.style.SUCCESS(f"Vehículo DESARME: {vehiculo.id}"))
        self.stdout.write(self.style.SUCCESS(f"Documento PTS: {documento.id}"))

    def _cleanup_demo(self, empresa):
        from taller.models.vehiculo_financial import VehicleFinancialEvent
        from taller.models.documento import Documento
        from taller.models.pieza_desarme import PiezaDesarme
        from taller.models.vehiculos import Vehiculo
        from taller.models.vehiculo_desarme import VehiculoDesarme

        documento_ids = Documento.objects.filter(
            empresa=empresa,
            observaciones__icontains="seed_desarme_demo",
        ).values_list("id", flat=True)
        VehicleFinancialEvent.objects.filter(empresa=empresa, descripcion__icontains="demo").delete()
        PiezaDesarme.objects.filter(empresa=empresa, codigo__in=["ENG-BMW-01", "TRS-BMW-01", "DOOR-BMW-01"]).delete()
        VehiculoDesarme.objects.filter(empresa=empresa, patente="BMW320").delete()
        Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME, patente="BMW320").delete()
        Documento.objects.filter(id__in=documento_ids).delete()
        self.stdout.write(self.style.WARNING("⚠️ Demo anterior eliminado."))
