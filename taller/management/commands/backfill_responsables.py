from django.core.management import BaseCommand
from django.db import transaction

from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)


class Command(BaseCommand):
    help = "Rellena tecnico_responsable en líneas desde el documento cuando esté vacío."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar qué se haría sin ejecutar cambios",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN - No se realizarán cambios"))

        # Procesar LineaServicio
        qs_servicio = LineaServicio.objects.filter(
            tecnico_responsable__isnull=True,
            documento__tecnico_responsable__isnull=False,
        )

        updated_servicio = 0
        for ls in qs_servicio.iterator():
            if not dry_run:
                ls.tecnico_responsable = ls.documento.tecnico_responsable
                ls.save(update_fields=["tecnico_responsable"])
            updated_servicio += 1

        # Procesar LineaRepuesto
        qs_repuesto = LineaRepuesto.objects.filter(
            tecnico_responsable__isnull=True,
            documento__tecnico_responsable__isnull=False,
        )

        updated_repuesto = 0
        for lr in qs_repuesto.iterator():
            if not dry_run:
                lr.tecnico_responsable = lr.documento.tecnico_responsable
                lr.save(update_fields=["tecnico_responsable"])
            updated_repuesto += 1

        # Procesar LineaOtroServicio
        qs_otro = LineaOtroServicio.objects.filter(
            tecnico_responsable__isnull=True,
            documento__tecnico_responsable__isnull=False,
        )

        updated_otro = 0
        for lo in qs_otro.iterator():
            if not dry_run:
                lo.tecnico_responsable = lo.documento.tecnico_responsable
                lo.save(update_fields=["tecnico_responsable"])
            updated_otro += 1

        total_updated = updated_servicio + updated_repuesto + updated_otro

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Actualizadas: {updated_servicio} líneas de servicio, "
                f"{updated_repuesto} líneas de repuesto, "
                f"{updated_otro} líneas de otro servicio"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"📊 Total: {total_updated} líneas procesadas"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("💡 Para ejecutar los cambios reales, ejecuta sin --dry-run")
            )
