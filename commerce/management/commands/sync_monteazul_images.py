import hashlib
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from commerce.models import CommerceProduct, ProductImage


INDEX_PATH = Path(settings.MEDIA_ROOT) / "commerce" / "image_index.json"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}

BLOCKED_TERMS = (
    "/puntas/",
    "gemini_generated",
    "fondo",
    "empaque",
    "empaquetadura",
    "banner_",
    "logo",
    "favicon",
    "placeholder",
    "removebg-preview",
)

PATH_PRIORITY = (
    "/import_media/productos/",
    "/media/productos/silenciadores/",
    "/media/productos/flexibles/",
    "/media/productos/cataliticos/",
    "/media/productos/resonadores/",
    "/imagenes/",
    "/onedrive-catalogo/",
    "/onedrive-monteazul/",
)


def normalize(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def file_hash(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def path_priority(path):
    text = str(path).lower()

    for index, marker in enumerate(PATH_PRIORITY):
        if marker in text:
            return index

    return 99


def valid_path(path):
    text = str(path).lower()

    return (
        path.is_file()
        and path.suffix.lower() in ALLOWED_EXTENSIONS
        and not any(term in text for term in BLOCKED_TERMS)
    )


def product_codes(product):
    values = (
        product.part_number,
        product.slug,
    )

    result = []

    for value in values:
        code = normalize(value)

        if not code:
            continue

        result.append(code)

        # Quitar únicamente sufijos artificiales del slug con guion:
        # lt1259-1 -> lt1259, 2x6-1 -> 2x6.
        raw_value = (value or "").lower().strip()
        if re.search(r"-[12]$", raw_value):
            stripped = normalize(re.sub(r"-[12]$", "", raw_value))
            if stripped and stripped != code:
                result.append(stripped)

    unique = []

    for code in result:
        if code not in unique:
            unique.append(code)

    return unique


def filename_matches(filename, codes):
    stem = normalize(Path(filename).stem)

    if not stem:
        return False

    for code in codes:
        if stem == code:
            return True

        # Variantes de la misma fotografía: DW004_1, DW004_2, DW004 (2).
        if re.fullmatch(re.escape(code) + r"[1-4]", stem):
            return True

    return False


def find_candidates(product, image_index):
    codes = product_codes(product)
    paths = []

    for filename, indexed_paths in image_index.items():
        if not filename_matches(filename, codes):
            continue

        for raw_path in indexed_paths:
            path = Path(raw_path)

            if valid_path(path):
                paths.append(path)

    # Eliminar copias binarias idénticas.
    unique_by_hash = {}

    for path in paths:
        try:
            digest = file_hash(path)
        except OSError:
            continue

        current = unique_by_hash.get(digest)

        if current is None or path_priority(path) < path_priority(current):
            unique_by_hash[digest] = path

    return sorted(
        unique_by_hash.values(),
        key=lambda path: (
            path_priority(path),
            -path.stat().st_size,
            str(path).lower(),
        ),
    )[:4]


class Command(BaseCommand):
    help = "Sincroniza imágenes originales verificadas para productos MonteAzul."

    def add_arguments(self, parser):
        parser.add_argument("--empresa", type=int, required=True)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        empresa_id = options["empresa"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        if not INDEX_PATH.is_file():
            raise CommandError(f"No existe el índice: {INDEX_PATH}")

        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        image_index = data.get("index", {})

        products = (
            CommerceProduct.objects
            .filter(empresa_id=empresa_id)
            .select_related("repuesto", "category")
            .prefetch_related("images")
            .order_by("id")
        )

        already_with_images = 0
        matched_products = 0
        created_images = 0
        without_match = 0
        processed_matches = 0

        for product in products:
            if product.images.exists():
                already_with_images += 1
                continue

            candidates = find_candidates(product, image_index)

            if not candidates:
                without_match += 1
                continue

            if limit is not None and processed_matches >= limit:
                break

            processed_matches += 1
            matched_products += 1

            self.stdout.write("")
            self.stdout.write(
                f"PRODUCTO id={product.pk} "
                f"codigo={product.part_number} "
                f"slug={product.slug}"
            )

            for position, source in enumerate(candidates, start=1):
                self.stdout.write(
                    f"  POS={position} "
                    f"SIZE={source.stat().st_size} "
                    f"ORIGEN={source}"
                )

            if dry_run:
                continue

            with transaction.atomic():
                for position, source in enumerate(candidates, start=1):
                    image = ProductImage(
                        commerce_product=product,
                        alt_text=product.nombre[:160],
                        is_primary=(position == 1),
                        position=position,
                    )

                    with source.open("rb") as handle:
                        image.image.save(source.name, File(handle), save=True)

                    created_images += 1

        self.stdout.write("")
        self.stdout.write("===== RESUMEN =====")
        self.stdout.write(f"PRODUCTOS_CON_IMAGEN_PREVIA={already_with_images}")
        self.stdout.write(f"PRODUCTOS_COINCIDENTES={matched_products}")
        self.stdout.write(f"PRODUCTOS_SIN_MATCH={without_match}")
        self.stdout.write(f"IMAGENES_CREADAS={created_images}")
        self.stdout.write(f"DRY_RUN={dry_run}")
