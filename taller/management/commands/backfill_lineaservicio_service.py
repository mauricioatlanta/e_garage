"""
Backfill LineaServicio.service desde LineaServicio.servicio (legacy).
Resuelve Service por empresa + code (codigo_interno o LEGACY-{id}).

Uso:
  python manage.py backfill_lineaservicio_service
  python manage.py backfill_lineaservicio_service --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = "Backfill LineaServicio.service desde LineaServicio.servicio (legacy)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Simular sin guardar.")

    def handle(self, *args, **opts):
        dry = bool(opts.get("dry_run", False))

        LineaServicio = apps.get_model("taller", "LineaServicio")
        Service = apps.get_model("taller", "Service")

        qs = LineaServicio.objects.filter(servicio__isnull=False).select_related(
            "documento", "servicio", "documento__empresa"
        )
        total = qs.count()
        self.stdout.write(f"Lineas a backfillear: {total}")

        updated = 0
        missing_target = 0

        ctx = transaction.atomic() if not dry else _nullcontext()
        with ctx:
            for linea in qs.iterator(chunk_size=500):
                empresa = linea.documento.empresa
                servicio = linea.servicio
                code = (getattr(servicio, "codigo_interno", None) or "").strip()
                if not code:
                    code = f"LEGACY-{servicio.id}"

                target = Service.objects.filter(empresa=empresa, code=code).first()
                if not target:
                    missing_target += 1
                    continue
                if linea.service_id != target.id:
                    if not dry:
                        linea.service = target
                        linea.save()
                    updated += 1

            if dry:
                self.stdout.write(self.style.WARNING("DRY-RUN: rollback intencional"))
                transaction.set_rollback(True)
                return

        self.stdout.write(self.style.SUCCESS("Backfill LineaServicio.service OK"))
        self.stdout.write(f"updated={updated} missing_target={missing_target}")


class _nullcontext:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
