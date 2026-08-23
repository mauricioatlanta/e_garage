"""
import_chatarra_csv — management command.

Importador del catálogo de chatarra electrónica recuperado en CSV, para el
tenant Atlanta Reciclajes (o cualquier empresa de rubro RECYCLING). Fase 1:
solo prepara/valida el importador — no se ejecuta contra el CSV real hasta
que el negocio esté listo para poblar datos.

Columnas esperadas (encabezados en español, case-insensitive):
    codigo            (obligatoria) — identificador único dentro de la empresa
    nombre            (obligatoria)
    categoria         (opcional)    — se crea automáticamente si no existe
    unidad_medida     (opcional)    — "KG" o "UNIDAD" (default: KG)
    precio_compra     (opcional)    — decimal, admite coma o punto
    precio_venta      (opcional)    — decimal, admite coma o punto
    cantidad_stock    (opcional)    — decimal, admite coma o punto
    proveedor         (opcional)

Filas inválidas (código/nombre vacío, decimal no parseable) se reportan y se
saltan; el resto del archivo se sigue procesando.

Idempotente: usa update_or_create sobre (empresa, codigo), así que correr el
mismo CSV dos veces actualiza en vez de duplicar.

Usage:
    python manage.py import_chatarra_csv ruta/al/archivo.csv --empresa 42
    python manage.py import_chatarra_csv ruta/al/archivo.csv --empresa atlanta_reciclajes
    python manage.py import_chatarra_csv ruta/al/archivo.csv --empresa 42 --dry-run
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taller.models.empresa import Empresa
from taller.models.reciclaje import CategoriaChatarra, ProductoChatarra

REQUIRED_COLUMNS = {"codigo", "nombre"}
UNIDAD_VALUES = {choice[0] for choice in ProductoChatarra.UNIDAD_CHOICES}


def _parse_decimal(raw: str | None, field: str) -> Decimal:
    if raw is None or str(raw).strip() == "":
        return Decimal("0")
    text = str(raw).strip().replace("$", "").replace(" ", "")
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"'{field}' inválido: '{raw}'") from exc


def _resolve_empresa(identifier: str) -> Empresa:
    if identifier.isdigit():
        try:
            return Empresa.objects.get(pk=int(identifier))
        except Empresa.DoesNotExist as exc:
            raise CommandError(f"No existe Empresa con id={identifier}") from exc
    User = get_user_model()
    try:
        user = User.objects.get(username=identifier)
    except User.DoesNotExist as exc:
        raise CommandError(f"No existe usuario/empresa para --empresa='{identifier}'") from exc
    try:
        return user.empresa
    except Empresa.DoesNotExist as exc:
        raise CommandError(f"El usuario '{identifier}' no tiene Empresa asociada") from exc


class Command(BaseCommand):
    help = "Importa productos de chatarra electrónica desde un CSV a ProductoChatarra."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta al archivo CSV a importar.")
        parser.add_argument(
            "--empresa", required=True,
            help="ID numérico de Empresa, o username del usuario dueño del tenant.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Valida y reporta sin escribir en la base de datos.",
        )
        parser.add_argument(
            "--encoding", default="utf-8-sig",
            help="Encoding del CSV (default: utf-8-sig, tolera BOM de Excel).",
        )
        parser.add_argument(
            "--delimiter", default=",",
            help="Delimitador de columnas (default: ',').",
        )

    def handle(self, *args, **options):
        empresa = _resolve_empresa(options["empresa"])
        csv_path = options["csv_path"]
        dry_run = options["dry_run"]

        try:
            fh = open(csv_path, newline="", encoding=options["encoding"])
        except OSError as exc:
            raise CommandError(f"No se pudo abrir '{csv_path}': {exc}") from exc

        created = updated = skipped = 0
        errors: list[str] = []
        categoria_cache: dict[str, CategoriaChatarra] = {}

        with fh:
            reader = csv.DictReader(fh, delimiter=options["delimiter"])
            headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
            missing = REQUIRED_COLUMNS - headers
            if missing:
                raise CommandError(
                    f"Faltan columnas obligatorias en el CSV: {sorted(missing)}"
                )

            with transaction.atomic():
                for line_num, raw_row in enumerate(reader, start=2):
                    row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw_row.items()}
                    codigo = row.get("codigo", "")
                    nombre = row.get("nombre", "")
                    if not codigo or not nombre:
                        errors.append(f"Línea {line_num}: 'codigo' y 'nombre' son obligatorios (fila saltada).")
                        skipped += 1
                        continue

                    try:
                        precio_compra = _parse_decimal(row.get("precio_compra"), "precio_compra")
                        precio_venta = _parse_decimal(row.get("precio_venta"), "precio_venta")
                        cantidad_stock = _parse_decimal(row.get("cantidad_stock"), "cantidad_stock")
                    except ValueError as exc:
                        errors.append(f"Línea {line_num}: {exc} (fila saltada).")
                        skipped += 1
                        continue

                    unidad_medida = (row.get("unidad_medida") or ProductoChatarra.UNIDAD_KG).upper()
                    if unidad_medida not in UNIDAD_VALUES:
                        errors.append(
                            f"Línea {line_num}: unidad_medida '{unidad_medida}' inválida, "
                            f"se usa '{ProductoChatarra.UNIDAD_KG}' (fila no saltada)."
                        )
                        unidad_medida = ProductoChatarra.UNIDAD_KG

                    categoria = None
                    categoria_nombre = row.get("categoria")
                    if categoria_nombre:
                        cache_key = categoria_nombre.lower()
                        categoria = categoria_cache.get(cache_key)
                        if categoria is None:
                            categoria, _ = CategoriaChatarra.objects.get_or_create(
                                empresa=empresa, nombre=categoria_nombre
                            )
                            categoria_cache[cache_key] = categoria

                    defaults = {
                        "nombre": nombre,
                        "categoria": categoria,
                        "unidad_medida": unidad_medida,
                        "precio_compra": precio_compra,
                        "precio_venta": precio_venta,
                        "cantidad_stock": cantidad_stock,
                        "proveedor": row.get("proveedor") or None,
                        "origen_importacion": csv_path,
                    }

                    _obj, was_created = ProductoChatarra.objects.update_or_create(
                        empresa=empresa, codigo=codigo, defaults=defaults
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

                if dry_run:
                    transaction.set_rollback(True)

        for err in errors:
            self.stdout.write(self.style.WARNING(err))

        summary = (
            f"{'[DRY-RUN] ' if dry_run else ''}"
            f"Importación completa — creados: {created}, actualizados: {updated}, "
            f"saltados: {skipped}, errores: {len(errors)}"
        )
        self.stdout.write(self.style.SUCCESS(summary))
