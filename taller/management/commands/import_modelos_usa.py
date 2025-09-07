"""
Comando de gestión para importar marcas y modelos de vehículos
desde el CSV generado por el scraper de VehiclesAPI (USA 1970-presente)
"""

import csv
import pathlib

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from taller.models.catalogo import CatalogoModeloAuto


class Command(BaseCommand):
    help = (
        "Importa Marca,Modelo desde el CSV generado por el scraper (USA 1970–presente)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default=r"E:\Usuarios\Mauricio\Descargas\usa_models_toolkit\output\models_us_1970_present.csv",
            help="Ruta al CSV Marca,Modelo",
        )
        parser.add_argument(
            "--chunk",
            type=int,
            default=5000,
            help="Tamaño de lote para bulk_create (default: 5000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra estadísticas sin importar datos",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpia la tabla antes de importar (¡CUIDADO!)",
        )

    def handle(self, *args, **options):
        csv_path = pathlib.Path(options["csv"])
        chunk_size = options["chunk"]
        is_dry_run = options["dry_run"]
        clear_first = options["clear"]

        # Validar que el archivo existe
        if not csv_path.exists():
            raise CommandError(f"❌ CSV no encontrado: {csv_path}")

        self.stdout.write(f"📂 Procesando: {csv_path}")
        self.stdout.write(f"📦 Tamaño de lote: {chunk_size}")

        # Limpiar tabla si se solicita
        if clear_first:
            if is_dry_run:
                current_count = CatalogoModeloAuto.objects.count()
                self.stdout.write(
                    f"🗑️  DRY-RUN: Se eliminarían {current_count} registros"
                )
            else:
                deleted_count = CatalogoModeloAuto.objects.count()
                CatalogoModeloAuto.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"🗑️  Eliminados {deleted_count} registros existentes"
                    )
                )

        # Leer y procesar CSV
        try:
            rows = []
            duplicados = 0
            lineas_vacias = 0

            with csv_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)

                for line_num, record in enumerate(
                    reader, start=2
                ):  # +2 porque line 1 es header
                    marca = (record.get("Marca") or "").strip()
                    modelo = (record.get("Modelo") or "").strip()

                    if not marca or not modelo:
                        lineas_vacias += 1
                        continue

                    # Normalización básica
                    marca = marca.title()
                    modelo = modelo.strip()

                    rows.append(CatalogoModeloAuto(marca=marca, modelo=modelo))

            total_filas = len(rows)
            self.stdout.write(f"📊 Leídas {total_filas} filas válidas")
            if lineas_vacias > 0:
                self.stdout.write(f"⚠️  Saltadas {lineas_vacias} filas vacías")

            if is_dry_run:
                # Solo mostrar estadísticas
                marcas_unicas = len(set(row.marca for row in rows))
                self.stdout.write(f"🏷️  Marcas únicas: {marcas_unicas}")
                self.stdout.write(f"🚗 Modelos únicos: {total_filas}")
                self.stdout.write("✅ DRY-RUN completado - no se insertaron datos")
                return

            # Insertar en base de datos
            self.stdout.write(f"💾 Insertando {total_filas} registros...")
            start_time = timezone.now()
            created_count = 0

            with transaction.atomic():
                for i in range(0, len(rows), chunk_size):
                    chunk = rows[i : i + chunk_size]

                    # bulk_create con ignore_conflicts evita errores por duplicados
                    created = CatalogoModeloAuto.objects.bulk_create(
                        chunk, ignore_conflicts=True
                    )
                    created_count += len(created)

                    # Progreso cada chunk
                    progress = ((i + len(chunk)) / len(rows)) * 100
                    self.stdout.write(f"⏳ Progreso: {progress:.1f}%")

            # Estadísticas finales
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            total_db = CatalogoModeloAuto.objects.count()
            marcas_db = CatalogoModeloAuto.objects.values("marca").distinct().count()

            self.stdout.write(self.style.SUCCESS("✅ Importación completada"))
            self.stdout.write(f"📈 Registros en DB: {total_db}")
            self.stdout.write(f"🏷️  Marcas únicas: {marcas_db}")
            self.stdout.write(f"⚡ Tiempo: {duration:.2f}s")
            self.stdout.write(f"🚀 Velocidad: {total_filas/duration:.0f} registros/seg")

        except Exception as e:
            raise CommandError(f"❌ Error procesando CSV: {e}")

    def _get_top_marcas_preview(self, limit=10):
        """Muestra las marcas más populares para verificación"""
        from django.db.models import Count

        top_marcas = (
            CatalogoModeloAuto.objects.values("marca")
            .annotate(count=Count("modelo"))
            .order_by("-count")[:limit]
        )

        self.stdout.write("🔝 Top marcas:")
        for marca in top_marcas:
            self.stdout.write(f"   • {marca['marca']}: {marca['count']} modelos")
