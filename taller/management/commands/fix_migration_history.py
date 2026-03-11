"""
Corrige historial de migraciones inconsistentes insertando registros faltantes.
Ejecutar solo si migrate falla con InconsistentMigrationHistory.

Uso: python manage.py fix_migration_history
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


MIGRATIONS_TO_INSERT = [
    ("taller", "0074_ops_ingreso_registro_checklist"),
    ("taller", "0075_add_documento_context_and_sequence_serie"),
    ("taller", "0076_add_linearepuesto_source_type"),
    ("taller", "0077_configuracionempresa_sales_tax_rate"),
    ("taller", "0078_merge_0075_0077"),
]


class Command(BaseCommand):
    help = "Inserta migraciones faltantes en django_migrations para corregir InconsistentMigrationHistory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Solo mostrar lo que se insertaría"
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        recorder = MigrationRecorder(connection)
        applied = {row[1] for row in recorder.applied_migrations() if row[0] == "taller"}
        to_insert = [m for m in MIGRATIONS_TO_INSERT if m[1] not in applied]
        if not to_insert:
            self.stdout.write(self.style.SUCCESS("No hay migraciones pendientes de insertar."))
            return
        if dry_run:
            self.stdout.write(f"Se insertarían: {[m[1] for m in to_insert]}")
            return
        for app, name in to_insert:
            try:
                recorder.record_applied(app, name)
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    self.stdout.write(f"  (ya existe: {name})")
                else:
                    raise
        self.stdout.write(
            self.style.SUCCESS(
                f"Insertadas {len(to_insert)} migraciones. Ejecute: python manage.py migrate taller"
            )
        )
