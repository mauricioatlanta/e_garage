"""
Importa catálogo USA de marcas/modelos desde CSV y consolida rangos por año.

Soporta dos formatos:
- Formato anual: marca, modelo, anio (una fila por año) → agrupa y consolida
  rangos consecutivos (ej. 2020,2021,2022 → 2020–2022).
- Formato rango: marca, modelo, anio_desde, anio_hasta → importación directa.

Requisitos:
- Migraciones aplicadas (incl. 0089_catalogo_anio_desde_hasta) para anio_desde/anio_hasta.
- Ruta al CSV: puede ser relativa al directorio de trabajo (ej. data/archivo.csv)
  o absoluta (ej. /srv/egarage/data/catalogo_usa_full.csv). En servidor, asegurar
  que el archivo exista en esa ruta o usar --csv /ruta/absoluta/al/archivo.csv.

Uso recomendado para carga maestra:
  python manage.py import_modelos_usa --csv data/catalogo_usa_full.csv --clear
"""

import csv
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taller.models.catalogo import CatalogoModeloAuto


class Command(BaseCommand):
    help = "Importa catálogo USA de marcas/modelos desde CSV y consolida rangos por año."

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="Ruta al archivo CSV")
        parser.add_argument("--dry-run", action="store_true", help="Simula sin guardar")
        parser.add_argument("--clear", action="store_true", help="Borra catálogo antes de importar")
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=5000,
            help="Tamaño de lote para bulk_create",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        dry_run = options["dry_run"]
        clear = options["clear"]
        chunk_size = options["chunk_size"]

        if not csv_path.exists():
            abs_path = csv_path.resolve()
            raise CommandError(
                f"No existe el archivo CSV: {csv_path}\n"
                f"  (resuelto: {abs_path}).\n"
                "  Use una ruta absoluta si ejecuta desde otro directorio, "
                "o cree el archivo/carpeta en el servidor."
            )

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            if not fieldnames:
                raise CommandError("El CSV no tiene encabezados")

            normalized_fields = {c.lower().strip(): c for c in fieldnames}

            has_single_year = "anio" in normalized_fields or "year" in normalized_fields
            has_range = "anio_desde" in normalized_fields or "anio_hasta" in normalized_fields

            rows = list(reader)

        if has_single_year:
            self._import_from_year_rows(rows, dry_run=dry_run, clear=clear, chunk_size=chunk_size)
        elif has_range:
            self._import_from_range_rows(rows, dry_run=dry_run, clear=clear, chunk_size=chunk_size)
        else:
            raise CommandError(
                "El CSV debe tener columna 'anio' o 'year' (modo anual) "
                "o 'anio_desde' y 'anio_hasta' (modo rango)."
            )

    def _get_value(self, row, *keys):
        """Obtiene valor de la fila por clave; prueba claves en orden (case-insensitive)."""
        row_lower = {k.strip().lower(): (v if v is not None else "") for k, v in row.items()}
        for key in keys:
            k = (key or "").strip().lower()
            if k in row_lower:
                val = row_lower[k]
                if val is not None and str(val).strip() != "":
                    return str(val).strip()
        return ""

    def _normalize_brand(self, value):
        """Trim sin alterar mayúsculas (GMC, BMW, RAM)."""
        return (value or "").strip()

    def _normalize_model(self, value):
        return (value or "").strip()

    def _compress_years(self, years):
        """
        Recibe lista de años ordenados y devuelve lista de rangos:
        [2018, 2019, 2020, 2022] -> [(2018, 2020), (2022, 2022)]
        """
        if not years:
            return []

        ranges = []
        start = years[0]
        prev = years[0]

        for year in years[1:]:
            if year == prev + 1:
                prev = year
            else:
                ranges.append((start, prev))
                start = year
                prev = year

        ranges.append((start, prev))
        return ranges

    def _import_from_year_rows(self, rows, dry_run=False, clear=False, chunk_size=5000):
        grouped = defaultdict(set)
        skipped = 0

        for idx, row in enumerate(rows, start=2):
            marca = self._normalize_brand(self._get_value(row, "marca", "Marca", "make", "Make"))
            modelo = self._normalize_model(
                self._get_value(row, "modelo", "Modelo", "model", "Model")
            )
            anio_raw = self._get_value(row, "anio", "Anio", "Año", "year", "Year")

            if not marca or not modelo or not anio_raw:
                skipped += 1
                continue

            if not anio_raw.isdigit():
                skipped += 1
                continue

            anio = int(anio_raw)
            grouped[(marca, modelo)].add(anio)

        objects = []

        for (marca, modelo), years_set in grouped.items():
            years = sorted(years_set)
            ranges = self._compress_years(years)

            for anio_desde, anio_hasta in ranges:
                objects.append(
                    CatalogoModeloAuto(
                        marca=marca,
                        modelo=modelo,
                        anio_desde=anio_desde,
                        anio_hasta=anio_hasta,
                        activo=True,
                    )
                )

        self._save_objects(
            objects,
            dry_run=dry_run,
            clear=clear,
            chunk_size=chunk_size,
            skipped=skipped,
            mode_label="modo anual consolidado",
        )

    def _import_from_range_rows(self, rows, dry_run=False, clear=False, chunk_size=5000):
        objects = []
        skipped = 0

        for idx, row in enumerate(rows, start=2):
            marca = self._normalize_brand(self._get_value(row, "marca", "Marca", "make", "Make"))
            modelo = self._normalize_model(
                self._get_value(row, "modelo", "Modelo", "model", "Model")
            )
            anio_desde_raw = self._get_value(
                row,
                "anio_desde",
                "Anio_Desde",
                "Año_Desde",
                "ano_desde",
                "year_from",
                "Year_From",
            )
            anio_hasta_raw = self._get_value(
                row,
                "anio_hasta",
                "Anio_Hasta",
                "Año_Hasta",
                "ano_hasta",
                "year_to",
                "Year_To",
            )

            if not marca or not modelo:
                skipped += 1
                continue

            anio_desde = (
                int(anio_desde_raw) if anio_desde_raw and anio_desde_raw.isdigit() else None
            )
            anio_hasta = (
                int(anio_hasta_raw) if anio_hasta_raw and anio_hasta_raw.isdigit() else None
            )

            if anio_desde is not None and anio_hasta is not None and anio_desde > anio_hasta:
                skipped += 1
                continue

            objects.append(
                CatalogoModeloAuto(
                    marca=marca,
                    modelo=modelo,
                    anio_desde=anio_desde,
                    anio_hasta=anio_hasta,
                    activo=True,
                )
            )

        self._save_objects(
            objects,
            dry_run=dry_run,
            clear=clear,
            chunk_size=chunk_size,
            skipped=skipped,
            mode_label="modo rango directo",
        )

    def _save_objects(
        self,
        objects,
        dry_run=False,
        clear=False,
        chunk_size=5000,
        skipped=0,
        mode_label="",
    ):
        self.stdout.write(f"Objetos preparados: {len(objects)}")
        self.stdout.write(f"Filas omitidas: {skipped}")
        self.stdout.write(f"Modo detectado: {mode_label}")

        if dry_run:
            for obj in objects[:20]:
                self.stdout.write(
                    f"  [DRY RUN] {obj.marca} | {obj.modelo} | "
                    f"{obj.anio_desde} | {obj.anio_hasta}"
                )
            if len(objects) > 20:
                self.stdout.write(self.style.WARNING(f"  ... y {len(objects) - 20} más"))
            return

        with transaction.atomic():
            if clear:
                deleted, _ = CatalogoModeloAuto.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Catálogo eliminado: {deleted} registros"))

            for i in range(0, len(objects), chunk_size):
                batch = objects[i : i + chunk_size]
                CatalogoModeloAuto.objects.bulk_create(batch, batch_size=chunk_size)

        self.stdout.write(self.style.SUCCESS("Importación finalizada correctamente"))
        self.stdout.write(f"Registros insertados: {len(objects)}")
