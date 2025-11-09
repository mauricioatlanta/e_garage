from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models import Cliente, Documento, Empresa, Tecnico, Vehiculo


class Command(BaseCommand):
    help = "Smoke test funcional mínimo para verificar que los modelos funcionan"

    def handle(self, *args, **options):
        self.stdout.write("🧪 Ejecutando smoke test funcional...")

        try:
            # Crear empresa
            emp, created = Empresa.objects.get_or_create(
                nombre="Demo US", pais="US", moneda="USD"
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Empresa creada: {emp.nombre}")
                )
            else:
                self.stdout.write(f"✅ Empresa existente: {emp.nombre}")

            # Crear técnico
            tec, created = Tecnico.objects.get_or_create(
                empresa=emp, nombre="Alex Tech", activo=True
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Técnico creado: {tec.nombre}")
                )
            else:
                self.stdout.write(f"✅ Técnico existente: {tec.nombre}")

            # Crear cliente
            cli, created = Cliente.objects.get_or_create(
                empresa=emp, nombre="John Doe", rut_ein="12-3456789"
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Cliente creado: {cli.nombre}")
                )
            else:
                self.stdout.write(f"✅ Cliente existente: {cli.nombre}")

            # Crear vehículo
            veh, created = Vehiculo.objects.get_or_create(
                empresa=emp,
                cliente=cli,
                vin="TESTVIN123",
                marca="Ford",
                modelo="F-150",
                patente="ABC123",
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Vehículo creado: {veh.marca} {veh.modelo}")
                )
            else:
                self.stdout.write(f"✅ Vehículo existente: {veh.marca} {veh.modelo}")

            # Crear documento
            doc = Documento.objects.create(
                empresa=emp,
                cliente=cli,
                vehiculo=veh,
                tipo="OT",
                estado="borrador",
                fecha_emision=timezone.now().date(),
                tecnico_responsable=tec,
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Documento creado: ID {doc.pk}"))

            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Smoke test exitoso! Documento ID: {doc.pk}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error en smoke test: {e}"))
            raise
