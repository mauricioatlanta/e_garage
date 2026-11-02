from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio


class Command(BaseCommand):
    help = "Crear líneas de documento de prueba para solucionar totales en $0"

    def handle(self, *args, **options):
        # Buscar el primer documento
        documento = Documento.objects.first()
        if not documento:
            self.stdout.write(self.style.ERROR("❌ No hay documentos en la base de datos"))
            return

        self.stdout.write(f"📄 Trabajando con documento: {documento.numero} ({documento.tipo})")

        # Agregar líneas de repuesto si no existen
        if not documento.lineas_repuesto.exists():
            LineaRepuesto.objects.create(
                documento=documento,
                codigo="REP001",
                nombre="Filtro de Aceite",
                cantidad=2,
                precio_unitario=Decimal("15000.00"),
                descuento=Decimal("0.00"),
            )

            LineaRepuesto.objects.create(
                documento=documento,
                codigo="REP002",
                nombre="Pastillas de Freno",
                cantidad=1,
                precio_unitario=Decimal("45000.00"),
                descuento=Decimal("10.00"),
            )
            self.stdout.write(self.style.SUCCESS("✅ Líneas de repuesto agregadas"))

        # Agregar líneas de servicio si no existen
        if not documento.lineas_servicio.exists():
            LineaServicio.objects.create(
                documento=documento,
                codigo="SER001",
                nombre="Cambio de Aceite",
                cantidad=1,
                precio_unitario=Decimal("25000.00"),
                descuento=Decimal("0.00"),
            )

            LineaServicio.objects.create(
                documento=documento,
                codigo="SER002",
                nombre="Revisión General",
                cantidad=1,
                precio_unitario=Decimal("35000.00"),
                descuento=Decimal("5.00"),
            )
            self.stdout.write(self.style.SUCCESS("✅ Líneas de servicio agregadas"))

        # Verificar totales
        self.stdout.write("\n📊 TOTALES:")
        self.stdout.write(f"   Repuestos: ${documento.total_repuestos()}")
        self.stdout.write(f"   Servicios: ${documento.total_servicios()}")
        self.stdout.write(f"   Total: ${documento.total_general()}")

        self.stdout.write(
            self.style.SUCCESS("\n🎉 Datos creados. Recargar la vista para ver los totales!")
        )
