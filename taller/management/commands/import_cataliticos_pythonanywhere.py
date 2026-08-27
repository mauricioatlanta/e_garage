"""
import_cataliticos_pythonanywhere — management command.

Recuperación única de los datos reales de Atlanta Reciclajes desde la base
SQLite del proyecto original (PythonAnywhere, "cataliticos"), cuya cuenta
fue cerrada por falta de pago. Migra:

    - cataliticos_catalitico     -> taller.Catalitico       (catálogo actual)
    - cataliticos_cliente        -> taller.Cliente           (vendedores)
    - cataliticos_compracatalitico
      + cataliticos_detallecatalitico
                                 -> taller.CompraReciclaje
                                    + DetalleCompraCatalitico (historial)

El catálogo (Catalitico) se importa con su estado ACTUAL (precio, stock,
vendido) tal cual estaba en el snapshot recuperado — no se re-simula la
lógica de "comprar incrementa stock" para las compras históricas, porque
ya no reflejarían el stock real de hoy. Las compras se insertan solo como
registro histórico/auditoría, preservando la fecha original (bypass de
auto_now_add vía update() posterior a la creación).

Idempotente:
    - Catalitico: update_or_create por (empresa, codigo).
    - Cliente: update_or_create por (empresa, tax_id) si hay RUT, si no por
      (empresa, telefono), si no por (empresa, nombre, apellido).
    - CompraReciclaje: se salta si ya existe una con
      f"[pythonanywhere:compra:{id_original}]" en notas.

Usage:
    python manage.py import_cataliticos_pythonanywhere ruta/db.sqlite3 \
        --empresa atlantareciclajes --media-dir ruta/media/cataliticos \
        --dry-run
"""
from __future__ import annotations

import re
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.reciclaje import (
    Catalitico,
    CompraReciclaje,
    DetalleCompraCatalitico,
)

IMPORT_TAG_PREFIX = "[pythonanywhere:compra:"


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


def _to_decimal(value) -> Decimal:
    if value is None or str(value).strip() == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal("0")


def _primera_marca(descripcion: str | None) -> str:
    """El campo original 'descripcion' a veces trae más de una marca
    compatible separadas por salto de línea (ej. "Peugeot\\nCitroen").
    Se usa solo la primera como marca_vehiculo; el texto completo se
    conserva en observaciones."""
    if not descripcion:
        return ""
    primera = descripcion.strip().splitlines()[0].strip()
    return primera[:100]


def _limpiar_rut(rut: str | None) -> str:
    if not rut:
        return ""
    return re.sub(r"\s+", "", rut.strip())


class Command(BaseCommand):
    help = (
        "Importa el catálogo, clientes y compras reales de Atlanta Reciclajes "
        "recuperados de la base SQLite del proyecto original (PythonAnywhere)."
    )

    def add_arguments(self, parser):
        parser.add_argument("sqlite_path", help="Ruta al db.sqlite3 recuperado.")
        parser.add_argument(
            "--empresa", required=True,
            help="ID numérico de Empresa, o username del usuario dueño del tenant.",
        )
        parser.add_argument(
            "--media-dir", default=None,
            help=(
                "Carpeta local que contiene directamente los archivos de imagen "
                "(equivalente a media/cataliticos/ del proyecto original — la "
                "carpeta que ya contiene GM02.jpeg, K181.jpeg, etc., no su "
                "padre). Si se omite, los catalíticos se importan sin imagen."
            ),
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Valida y reporta sin escribir en la base de datos.",
        )

    def handle(self, *args, **options):
        empresa = _resolve_empresa(options["empresa"])
        sqlite_path = options["sqlite_path"]
        media_dir = Path(options["media_dir"]) if options["media_dir"] else None
        dry_run = options["dry_run"]

        if not Path(sqlite_path).is_file():
            raise CommandError(f"No existe el archivo '{sqlite_path}'")

        src = sqlite3.connect(sqlite_path)
        src.row_factory = sqlite3.Row

        stats = {
            "catalitico_creado": 0, "catalitico_actualizado": 0,
            "catalitico_con_imagen": 0, "catalitico_sin_imagen": 0,
            "cliente_creado": 0, "cliente_actualizado": 0,
            "compra_creada": 0, "compra_saltada": 0,
            "detalle_creado": 0,
        }
        warnings: list[str] = []

        with transaction.atomic():
            catalitico_by_old_id: dict[int, Catalitico] = {}
            for row in src.execute("SELECT * FROM cataliticos_catalitico"):
                marca = _primera_marca(row["descripcion"])
                observaciones = (
                    f"Migrado desde PythonAnywhere (proyecto cataliticos, id original={row['id']}).\n"
                    f"Descripción original: {row['descripcion'] or ''}"
                ).strip()
                obj, created = Catalitico.objects.update_or_create(
                    empresa=empresa,
                    codigo=row["codigo"],
                    defaults={
                        "nombre": marca or row["codigo"],
                        "marca_vehiculo": marca,
                        "precio_compra": _to_decimal(row["valor_compra"]),
                        "precio_venta": _to_decimal(row["valor_venta"]),
                        "cantidad_stock": max(int(row["cantidad"] or 0), 0),
                        "estado": (
                            Catalitico.ESTADO_VENDIDO
                            if row["vendido"]
                            else Catalitico.ESTADO_DISPONIBLE
                        ),
                        "observaciones": observaciones,
                        "activo": True,
                    },
                )
                stats["catalitico_creado" if created else "catalitico_actualizado"] += 1
                catalitico_by_old_id[row["id"]] = obj

                imagen_rel = row["imagen_principal"]
                if imagen_rel and media_dir and not obj.imagen:
                    origen = media_dir / Path(imagen_rel).name
                    if origen.is_file():
                        if not dry_run:
                            with open(origen, "rb") as fh:
                                obj.imagen.save(Path(imagen_rel).name, ContentFile(fh.read()), save=True)
                        stats["catalitico_con_imagen"] += 1
                    else:
                        stats["catalitico_sin_imagen"] += 1
                        warnings.append(f"Catalítico {row['codigo']}: imagen no encontrada ({imagen_rel}).")
                elif imagen_rel:
                    stats["catalitico_sin_imagen"] += 1

            cliente_by_old_id: dict[int, Cliente] = {}
            for row in src.execute("SELECT * FROM cataliticos_cliente"):
                rut = _limpiar_rut(row["rut"])
                telefono = (row["telefono"] or "").strip() or None
                email = (row["correo"] or "").strip() or None
                apellido = (row["apellido"] or "").strip() or None
                defaults = {
                    "nombre": row["nombre"] or "Cliente",
                    "apellido": apellido,
                    "telefono": telefono,
                    "email": email,
                    "direccion": (row["direccion"] or "").strip() or None,
                    "tax_id": rut,
                }
                if rut:
                    obj, created = Cliente.objects.update_or_create(
                        empresa=empresa, tax_id=rut, defaults=defaults
                    )
                elif telefono:
                    obj, created = Cliente.objects.update_or_create(
                        empresa=empresa, telefono=telefono, defaults=defaults
                    )
                else:
                    obj, created = Cliente.objects.get_or_create(
                        empresa=empresa, nombre=defaults["nombre"], apellido=apellido,
                        defaults=defaults,
                    )
                stats["cliente_creado" if created else "cliente_actualizado"] += 1
                cliente_by_old_id[row["id"]] = obj

            for row in src.execute("SELECT * FROM cataliticos_compracatalitico"):
                tag = f"{IMPORT_TAG_PREFIX}{row['id']}]"
                if CompraReciclaje.objects.filter(empresa=empresa, notas__contains=tag).exists():
                    stats["compra_saltada"] += 1
                    continue

                cliente = cliente_by_old_id.get(row["cliente_id"]) if row["cliente_id"] else None
                compra = CompraReciclaje.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    notas=(
                        f"{tag} Migrado desde PythonAnywhere. "
                        f"Cliente original: {row['cliente_nombre']} {row['cliente_apellido']} "
                        f"({row['cliente_telefono']})."
                    ),
                )
                fecha = row["fecha"]
                if fecha and not dry_run:
                    CompraReciclaje.objects.filter(pk=compra.pk).update(
                        created_at=fecha, updated_at=fecha
                    )
                stats["compra_creada"] += 1

                detalles = src.execute(
                    "SELECT * FROM cataliticos_detallecatalitico WHERE compra_id = ?",
                    (row["id"],),
                ).fetchall()
                for det in detalles:
                    catalitico = catalitico_by_old_id.get(det["catalitico_id"])
                    if catalitico is None:
                        warnings.append(
                            f"Compra original #{row['id']}: catalítico original "
                            f"id={det['catalitico_id']} no encontrado, línea saltada."
                        )
                        continue
                    DetalleCompraCatalitico.objects.create(
                        compra=compra,
                        catalitico=catalitico,
                        cantidad=max(int(det["cantidad"] or 1), 1),
                        precio_unitario=_to_decimal(det["precio_unitario"]),
                    )
                    stats["detalle_creado"] += 1

            if dry_run:
                transaction.set_rollback(True)

        src.close()

        for w in warnings:
            self.stdout.write(self.style.WARNING(w))

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Catalíticos: {stats['catalitico_creado']} creados, "
            f"{stats['catalitico_actualizado']} actualizados "
            f"({stats['catalitico_con_imagen']} con imagen, "
            f"{stats['catalitico_sin_imagen']} sin imagen)."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Clientes: {stats['cliente_creado']} creados, "
            f"{stats['cliente_actualizado']} actualizados."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Compras: {stats['compra_creada']} creadas, "
            f"{stats['compra_saltada']} saltadas (ya importadas), "
            f"{stats['detalle_creado']} líneas de detalle creadas."
        ))
