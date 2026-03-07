"""
Backfill Documento.total para documentos que tienen líneas pero total=0 (stale).

Uso:
  python manage.py backfill_documento_totals
  python manage.py backfill_documento_totals --dry-run
  python manage.py backfill_documento_totals --ids 49 50 51
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.documento import Documento


class Command(BaseCommand):
    help = "Recalcula totales en documentos con total=0 que sí tienen líneas (repuestos/servicios/otros)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ids",
            nargs="*",
            type=int,
            help="IDs de documentos a procesar (si no se pasa, se procesan todos con total=0 y con líneas).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar cuántos se recalcularían, sin guardar.",
        )

    def handle(self, *args, **options):
        ids = options.get("ids")
        dry_run = options.get("dry_run", False)

        qs = Documento.objects.filter(total=0)
        if ids:
            qs = qs.filter(id__in=ids)

        total_candidatos = qs.count()
        # Solo los que tienen al menos una línea
        con_lineas = 0
        recalculados = 0

        for doc in qs.iterator():
            has_rep = doc.lineas_repuesto.exists()
            has_srv = doc.lineas_servicio.exists()
            has_otro = doc.lineas_otro_servicio.exists()
            if not (has_rep or has_srv or has_otro):
                continue
            con_lineas += 1
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f"[DRY-RUN] Doc {doc.id} tendría recálculo (tiene líneas)")
                )
                recalculados += 1
                continue
            with transaction.atomic():
                doc.recompute_totals(persist=True)
            recalculados += 1
            self.stdout.write(self.style.SUCCESS(f"Doc {doc.id}: total actualizado a {doc.total}"))

        self.stdout.write(
            self.style.NOTICE(
                f"Documentos con total=0: {total_candidatos}; con líneas: {con_lineas}; recalculados: {recalculados}"
            )
        )
