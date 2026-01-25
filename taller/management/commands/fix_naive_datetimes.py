"""
Management command para limpiar datetimes naive en la base de datos.

Uso:
  python manage.py fix_naive_datetimes --dry-run
  python manage.py fix_naive_datetimes
  python manage.py fix_naive_datetimes --model Documento
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db import connection
import pytz


class Command(BaseCommand):
    help = "Corrige datetimes naive convirtiéndolos a timezone-aware (asume UTC por defecto)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe cambios")
        parser.add_argument("--model", type=str, help="Modelo específico (ej: Documento)")

    def _get_datetime_fields(self, model):
        return [f.name for f in model._meta.get_fields() if f.__class__.__name__ == "DateTimeField"]

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        model_filter = options.get("model")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN: No se harán cambios reales\n"))

        default_tz = pytz.UTC  # asumimos UTC si venía naive

        # ✅ Si no especifican modelo: revisa TODOS los modelos de la app "taller"
        if not model_filter:
            models = list(apps.get_app_config("taller").get_models())
            models_to_check = [(m, self._get_datetime_fields(m)) for m in models]
            models_to_check = [(m, fields) for (m, fields) in models_to_check if fields]
        else:
            # ✅ Modelo específico por nombre dentro de la app "taller"
            try:
                model = apps.get_model("taller", model_filter)
            except LookupError:
                self.stdout.write(
                    self.style.ERROR(f"❌ Modelo '{model_filter}' no encontrado en app 'taller'")
                )
                return
            fields = self._get_datetime_fields(model)
            if not fields:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Modelo {model_filter} no tiene DateTimeField")
                )
                return
            models_to_check = [(model, fields)]

        total_fixed = 0

        for model, datetime_fields in models_to_check:
            self.stdout.write(
                f"\n📋 Verificando {model.__name__} (campos: {', '.join(datetime_fields)})"
            )

            # ✅ Validar existencia de tabla
            table = model._meta.db_table
            with connection.cursor() as cursor:
                # 1) tabla existe?
                tables = connection.introspection.table_names(cursor)
                if table not in tables:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️ Saltando {model.__name__}: no existe tabla {table}"
                        )
                    )
                    continue

                # 2) obtener columnas existentes
                cols = {
                    c.name for c in connection.introspection.get_table_description(cursor, table)
                }

            for field_name in datetime_fields:
                # ✅ Validar existencia de columna
                if field_name not in cols:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️ Saltando {model.__name__}.{field_name}: no existe columna en {table}"
                        )
                    )
                    continue
                fixed_count = 0
                try:
                    qs = model.objects.all()

                    for obj in qs.iterator(chunk_size=200):
                        value = getattr(obj, field_name, None)
                        if value is None:
                            continue

                        # naive = tzinfo None
                        if value.tzinfo is None:
                            aware_dt = timezone.make_aware(value, default_tz)

                            if not dry_run:
                                setattr(obj, field_name, aware_dt)
                                obj.save(update_fields=[field_name])

                            fixed_count += 1
                            if fixed_count <= 5:
                                self.stdout.write(
                                    f"  ✅ {model.__name__}#{obj.pk}.{field_name}: {value} → {aware_dt}"
                                )

                    if fixed_count:
                        total_fixed += fixed_count
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  📊 {fixed_count} registros corregidos en {field_name}"
                            )
                        )
                    else:
                        self.stdout.write(f"  ✓ {field_name}: Sin datetimes naive")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ Error procesando {model.__name__}.{field_name}: {e}"
                        )
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n🔍 DRY-RUN completado. Se corregirían {total_fixed} registros."
                )
            )
            self.stdout.write("   Ejecuta sin --dry-run para aplicar cambios.")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Limpieza completada. {total_fixed} registros corregidos.")
            )
