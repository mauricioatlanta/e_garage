"""
CatalogImporter — motor genérico para importar catálogos desde SQLite hacia Commerce.

Esquema SQLite esperado por defecto (sobreescribir TABLE_* / COL_* en subclases):
    categories(id, parent_id?, name, slug?, description?, is_active?)
    products(id, sku, name, slug?, category_id?, price, cost_price?, stock?,
             description?, deleted_at?)
    product_images(id, product_id, image, position?, is_primary?, alt_text?)
    product_compatibility(id, ...)   ← stub, fase 5

Idempotente:
  - Categorías: (empresa, slug)
  - Productos:  Repuesto.part_number == sku dentro de la empresa
  - Imágenes:   se omiten si el producto ya tiene imágenes (salvo --overwrite)

Reutilización para cualquier cliente:
    class MiClienteAdapter(CatalogImporter):
        TABLE_CATEGORIES = "mi_tabla_cats"
        COL_DESCRIPTION  = "ficha"
        IMAGE_SEARCH_DIRS = ("fotos",)
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from taller.models import Empresa

logger = logging.getLogger(__name__)

_MAX_IMAGES = 4


# ── Resultado ──────────────────────────────────────────────────────────────────

@dataclass
class CatalogImportResult:
    categories_created: int = 0
    categories_updated: int = 0
    products_created: int = 0
    products_updated: int = 0
    products_skipped: int = 0
    repuestos_created: int = 0
    images_copied: int = 0
    images_missing: int = 0
    images_skipped: int = 0
    compatibilities_pending: int = 0
    review_written_to: Path | None = None
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"Categorías: {self.categories_created} creadas, {self.categories_updated} actualizadas",
            f"Repuestos:  {self.repuestos_created} creados",
            f"Productos:  {self.products_created} creados, {self.products_updated} actualizados"
            + (f", {self.products_skipped} sin cambios" if self.products_skipped else ""),
            f"Imágenes:   {self.images_copied} copiadas"
            + (f", {self.images_missing} faltantes" if self.images_missing else "")
            + (f", {self.images_skipped} omitidas (ya existían)" if self.images_skipped else ""),
        ]
        if self.compatibilities_pending:
            lines.append(f"Compatibilidades pendientes (fase 5): {self.compatibilities_pending}")
        if self.review_written_to:
            lines.append(f"Revisión manual: {self.review_written_to}")
        if self.errors:
            lines.append(f"Errores: {len(self.errors)}")
        return " | ".join(lines)


# ── Motor genérico ─────────────────────────────────────────────────────────────

class CatalogImporter:
    """
    Motor de importación reutilizable para cualquier catálogo en formato SQLite.

    Sobreescribir TABLE_* / COL_* / IMAGE_SEARCH_DIRS en subclases para
    adaptar al esquema de cada proveedor sin duplicar la lógica de importación.
    """

    # ── Tabla de categorías ───────────────────────────────────────
    TABLE_CATEGORIES = "categories"
    TABLE_PRODUCTS   = "products"
    TABLE_IMAGES     = "product_images"
    TABLE_COMPAT     = "product_compatibility"

    # ── Columnas de TABLE_PRODUCTS ────────────────────────────────
    COL_SKU         = "sku"
    COL_NAME        = "name"
    COL_SLUG        = "slug"
    COL_CATEGORY_ID = "category_id"
    COL_PRICE       = "price"
    COL_COST        = "cost_price"
    COL_STOCK       = "stock"
    COL_DESCRIPTION = "description"
    COL_DELETED_AT  = "deleted_at"

    # ── Columnas de TABLE_IMAGES ──────────────────────────────────
    COL_IMG_FILE     = "image"
    COL_IMG_POSITION = "position"
    COL_IMG_PRIMARY  = "is_primary"
    COL_IMG_ALT      = "alt_text"

    # ── Directorios de búsqueda de imágenes (relativos a MEDIA_ROOT) ─
    IMAGE_SEARCH_DIRS: tuple[str, ...] = ()

    # ─────────────────────────────────────────────────────────────

    def __init__(
        self,
        db_path: str | Path,
        empresa: "Empresa",
        *,
        dry_run: bool = False,
        overwrite: bool = False,
        only_categories: bool = False,
        only_products: bool = False,
        only_images: bool = False,
        media_root: str | Path | None = None,
        review_output: str | Path | None = None,
        image_index_path: str | Path | None = None,
    ) -> None:
        self._db_path = Path(db_path)
        self._empresa = empresa
        self._dry_run = dry_run
        self._overwrite = overwrite
        self._only_categories = only_categories
        self._only_products = only_products
        self._only_images = only_images
        self._media_root = Path(media_root) if media_root else Path(settings.MEDIA_ROOT)
        self._review_output = Path(review_output) if review_output else None
        self._image_index_path = Path(image_index_path) if image_index_path else None
        self._run_all = not (only_categories or only_products or only_images)

    # ── Punto de entrada ──────────────────────────────────────────

    def run(self) -> CatalogImportResult:
        if not self._db_path.exists():
            raise FileNotFoundError(f"BD SQLite no encontrada: {self._db_path}")

        from commerce.services.catalog.media_resolver import MediaResolver
        self._resolver = MediaResolver(
            self._media_root,
            self.IMAGE_SEARCH_DIRS,
            index_path=self._image_index_path,
        )

        result = CatalogImportResult()
        con = sqlite3.connect(str(self._db_path))
        con.row_factory = sqlite3.Row

        try:
            category_map: dict[int, object] = {}
            product_map: dict[int, object] = {}

            if self._run_all or self._only_categories:
                category_map = self._import_categories(con, result)

            if self._run_all or self._only_products:
                if not category_map:
                    category_map = self._load_existing_categories(con)
                product_map = self._import_products(con, result, category_map)

            if self._run_all or self._only_images:
                if not product_map:
                    product_map = self._load_existing_product_map(con)
                self._import_images(con, result, product_map)

            self._count_compatibilities(con, result)

        finally:
            con.close()

        if not self._dry_run and self._resolver.has_issues:
            review_path = self._review_output or (self._db_path.parent / "manual_review.json")
            written = self._resolver.write_review_if_needed(
                review_path, empresa_id=self._empresa.pk
            )
            if written:
                result.review_written_to = review_path

        return result

    # ── Categorías ────────────────────────────────────────────────

    def _import_categories(
        self, con: sqlite3.Connection, result: CatalogImportResult
    ) -> dict[int, object]:
        from django.utils.text import slugify
        from commerce.models import CommerceCategory

        rows = _read_table(con, self.TABLE_CATEGORIES)
        ordered = _topological_sort(rows)
        category_map: dict[int, object] = {}

        for row in ordered:
            row_id = row["id"]
            name = (row.get("name") or "").strip()
            if not name:
                result.errors.append(f"Categoría id={row_id} sin nombre — omitida")
                continue

            slug = (row.get("slug") or "").strip() or slugify(name)[:140] or f"cat-{row_id}"
            description = (row.get("description") or "").strip()
            is_active = bool(row.get("is_active", 1))
            parent_id = row.get("parent_id")
            parent = category_map.get(parent_id) if parent_id else None

            if self._dry_run:
                exists = CommerceCategory.objects.filter(empresa=self._empresa, slug=slug).exists()
                print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} categoría: {slug}")
                if not exists:
                    result.categories_created += 1
                continue

            defaults = {
                "name": name,
                "description": description,
                "is_active": is_active,
                "parent": parent,
            }
            if self._overwrite:
                cat, created = CommerceCategory.objects.update_or_create(
                    empresa=self._empresa, slug=slug, defaults=defaults
                )
                result.categories_created += created
                result.categories_updated += not created
            else:
                cat, created = CommerceCategory.objects.get_or_create(
                    empresa=self._empresa, slug=slug, defaults=defaults
                )
                result.categories_created += created

            category_map[row_id] = cat

        return category_map

    def _load_existing_categories(self, con: sqlite3.Connection) -> dict[int, object]:
        from django.utils.text import slugify
        from commerce.models import CommerceCategory

        rows = _read_table(con, self.TABLE_CATEGORIES)
        category_map: dict[int, object] = {}
        for row in rows:
            slug = (row.get("slug") or "").strip() or slugify(row.get("name", ""))[:140]
            try:
                cat = CommerceCategory.objects.get(empresa=self._empresa, slug=slug)
                category_map[row["id"]] = cat
            except CommerceCategory.DoesNotExist:
                pass
        return category_map

    # ── Productos ─────────────────────────────────────────────────

    def _import_products(
        self,
        con: sqlite3.Connection,
        result: CatalogImportResult,
        category_map: dict,
    ) -> dict[int, object]:
        rows = _read_table(con, self.TABLE_PRODUCTS)
        product_map: dict[int, object] = {}

        for row in rows:
            if row.get(self.COL_DELETED_AT):
                continue

            sku = (row.get(self.COL_SKU) or "").strip()
            if not sku:
                result.errors.append(f"Producto id={row.get('id')} sin SKU — omitido")
                continue

            try:
                cp = self._import_one_product(row, sku, category_map, result)
                if cp is not None:
                    product_map[row["id"]] = cp
            except Exception as exc:
                result.errors.append(f"Producto '{sku}': {exc}")
                logger.exception("Error importando producto sku=%s", sku)

        return product_map

    def _import_one_product(self, row: dict, sku: str, category_map: dict, result: CatalogImportResult):
        from django.db import transaction
        from django.utils.text import slugify
        from taller.models.repuesto import Repuesto
        from commerce.models import CommerceProduct

        name = (row.get(self.COL_NAME) or sku).strip()
        slug = (row.get(self.COL_SLUG) or "").strip() or slugify(sku)[:280] or f"prod-{sku}"
        category = category_map.get(row.get(self.COL_CATEGORY_ID))
        description = (row.get(self.COL_DESCRIPTION) or "").strip()
        price = _to_decimal(row.get(self.COL_PRICE), Decimal("0"))
        cost = _to_decimal(row.get(self.COL_COST), Decimal("0"))
        stock = max(0, int(row.get(self.COL_STOCK) or 0))

        if self._dry_run:
            exists = Repuesto.objects.filter(empresa=self._empresa, part_number=sku).exists()
            print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} producto: {sku} — {name}")
            if exists:
                if self._overwrite:
                    result.products_updated += 1
                else:
                    result.products_skipped += 1
            else:
                result.products_created += 1
                result.repuestos_created += 1
            return True

        with transaction.atomic():
            rep_defaults = {
                "nombre": name,
                "precio_venta": price,
                "precio_compra": cost,
                "cantidad_stock": stock,
            }
            repuesto, rep_created = Repuesto.objects.get_or_create(
                empresa=self._empresa,
                part_number=sku,
                defaults=rep_defaults,
            )
            if rep_created:
                result.repuestos_created += 1
            elif self._overwrite:
                Repuesto.objects.filter(pk=repuesto.pk).update(**rep_defaults)
                repuesto.refresh_from_db()

            cp_defaults = {
                "category": category,
                "descripcion_larga": description,
                "is_publishable": True,
            }
            try:
                cp = CommerceProduct.objects.get(empresa=self._empresa, repuesto=repuesto)
                if self._overwrite:
                    for attr, val in cp_defaults.items():
                        setattr(cp, attr, val)
                    cp.save(update_fields=list(cp_defaults.keys()))
                    result.products_updated += 1
                else:
                    result.products_skipped += 1
            except CommerceProduct.DoesNotExist:
                cp = CommerceProduct.objects.create(
                    empresa=self._empresa,
                    repuesto=repuesto,
                    slug=slug,
                    **cp_defaults,
                )
                result.products_created += 1

        return cp

    def _load_existing_product_map(self, con: sqlite3.Connection) -> dict[int, object]:
        from taller.models.repuesto import Repuesto
        from commerce.models import CommerceProduct

        rows = _read_table(con, self.TABLE_PRODUCTS)
        product_map: dict[int, object] = {}
        for row in rows:
            sku = (row.get(self.COL_SKU) or "").strip()
            if not sku:
                continue
            try:
                rep = Repuesto.objects.get(empresa=self._empresa, part_number=sku)
                cp = CommerceProduct.objects.get(empresa=self._empresa, repuesto=rep)
                product_map[row["id"]] = cp
            except (Repuesto.DoesNotExist, CommerceProduct.DoesNotExist):
                pass
        return product_map

    # ── Imágenes ──────────────────────────────────────────────────

    def _import_images(
        self,
        con: sqlite3.Connection,
        result: CatalogImportResult,
        product_map: dict,
    ) -> None:
        try:
            rows = _read_table(con, self.TABLE_IMAGES)
        except ValueError:
            return

        by_product: dict[int, list] = {}
        for row in rows:
            pid = row.get("product_id")
            if pid is not None:
                by_product.setdefault(pid, []).append(row)

        for sqlite_pid, image_rows in by_product.items():
            cp = product_map.get(sqlite_pid)
            if cp is None:
                continue
            sorted_rows = sorted(
                image_rows,
                key=lambda r: (r.get(self.COL_IMG_POSITION) or 99, r.get("id") or 0),
            )
            self._import_product_images(cp, sorted_rows, result)

    def _import_product_images(self, cp, image_rows: list, result: CatalogImportResult) -> None:
        from commerce.models.product import ProductImage

        if not self._dry_run and not self._overwrite and cp.images.exists():
            result.images_skipped += len(image_rows)
            return

        if not self._dry_run and self._overwrite:
            cp.images.all().delete()

        imported = 0
        for row in image_rows[:_MAX_IMAGES]:
            db_path = (row.get(self.COL_IMG_FILE) or "").strip()
            if not db_path:
                result.images_missing += 1
                continue

            position = max(1, min(4, int(row.get(self.COL_IMG_POSITION) or (imported + 1))))
            is_primary = bool(row.get(self.COL_IMG_PRIMARY, imported == 0))
            alt_text = (row.get(self.COL_IMG_ALT) or "")[:160]

            phys = self._resolver.resolve(db_path)
            if phys is None:
                result.images_missing += 1
                continue

            if self._dry_run:
                print(f"  [dry-run] imagen ENCONTRADA: {db_path}")
                result.images_copied += 1
                imported += 1
                continue

            try:
                from django.core.files import File
                img = ProductImage(
                    commerce_product=cp,
                    alt_text=alt_text,
                    is_primary=is_primary,
                    position=position,
                )
                with phys.open("rb") as f:
                    img.image.save(phys.name, File(f), save=True)
                imported += 1
                result.images_copied += 1
            except Exception as exc:
                result.errors.append(f"Imagen '{db_path}': {exc}")
                result.images_missing += 1

    # ── Compatibilidades (stub fase 5) ────────────────────────────

    def _count_compatibilities(self, con: sqlite3.Connection, result: CatalogImportResult) -> None:
        try:
            cur = con.execute(f"SELECT COUNT(*) FROM {self.TABLE_COMPAT}")  # noqa: S608
            count = cur.fetchone()[0]
            result.compatibilities_pending = count
            if count:
                logger.info(
                    "Fase 5 pendiente: %d registros en %s listos para importar.",
                    count, self.TABLE_COMPAT,
                )
        except sqlite3.OperationalError:
            pass


# ── Utilidades de módulo ───────────────────────────────────────────────────────

def _read_table(con: sqlite3.Connection, table: str) -> list[dict]:
    try:
        cur = con.execute(f"SELECT * FROM {table} ORDER BY id")  # noqa: S608
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError as exc:
        raise ValueError(f"No se pudo leer la tabla '{table}': {exc}") from exc


def _topological_sort(rows: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in rows}
    visited: set[int] = set()
    result: list[dict] = []

    def visit(row_id: int) -> None:
        if row_id in visited:
            return
        visited.add(row_id)
        parent_id = by_id.get(row_id, {}).get("parent_id")
        if parent_id and parent_id in by_id:
            visit(parent_id)
        if row_id in by_id:
            result.append(by_id[row_id])

    for row in rows:
        visit(row["id"])

    return result


def _to_decimal(value, default) -> Decimal | None:
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return default
