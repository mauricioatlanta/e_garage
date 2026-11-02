"""
Tests del MonteAzulAdapter (CatalogImporter + esquema MonteAzul).

Usa el esquema real de MonteAzul:
  catalog_category, catalog_product, catalog_productimage, catalog_productcompatibility.

Principios:
  - BD SQLite en tmp_path (sin tocar archivos de producción).
  - Imágenes: tmp_path para archivos reales; paths inexistentes para probar skip.
  - Idempotencia verificada con doble importación.
  - dry_run no escribe ninguna fila.
  - products_skipped ≠ images_missing: la semántica de cada contador es distinta.
  - Tenant isolation verificado explícitamente.
  - Subclase con TABLE_* / COL_* sobreescritos verifica la reutilización del motor genérico.
"""
import sqlite3

import pytest

from commerce.services.catalog.adapters.monteazul import MonteAzulAdapter
from commerce.services.catalog.importer import CatalogImporter
from taller.tests.factories import EmpresaFactory


# ── Helpers de BD SQLite ──────────────────────────────────────────────────────

_DDL = """
CREATE TABLE catalog_category (
    id          INTEGER PRIMARY KEY,
    parent_id   INTEGER,
    name        TEXT NOT NULL,
    slug        TEXT,
    description TEXT DEFAULT '',
    is_active   INTEGER DEFAULT 1
);
CREATE TABLE catalog_product (
    id             INTEGER PRIMARY KEY,
    sku            TEXT UNIQUE NOT NULL,
    name           TEXT NOT NULL,
    slug           TEXT,
    category_id    INTEGER,
    price          REAL NOT NULL DEFAULT 0,
    cost_price     REAL DEFAULT 0,
    stock          INTEGER DEFAULT 0,
    ficha_tecnica  TEXT DEFAULT '',
    is_publishable INTEGER DEFAULT 0,
    quality_score  REAL DEFAULT 0,
    deleted_at     TEXT
);
CREATE TABLE catalog_productimage (
    id         INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    image      TEXT NOT NULL,
    position   INTEGER DEFAULT 1,
    is_primary INTEGER DEFAULT 0,
    alt_text   TEXT DEFAULT ''
);
CREATE TABLE catalog_productcompatibility (
    id          INTEGER PRIMARY KEY,
    product_id  INTEGER NOT NULL,
    marca       TEXT,
    modelo      TEXT,
    motor       TEXT,
    cilindrada  TEXT,
    anio_desde  INTEGER,
    anio_hasta  INTEGER,
    combustible TEXT
);
"""


def _make_db(tmp_path, *, categories=None, products=None, images=None, compatibilities=None):
    db_path = tmp_path / "monteazul.sqlite3"
    con = sqlite3.connect(str(db_path))
    con.executescript(_DDL)

    for row in (categories or []):
        con.execute(
            "INSERT INTO catalog_category (id, parent_id, name, slug, description, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (row.get("id"), row.get("parent_id"), row["name"], row.get("slug"),
             row.get("description", ""), int(row.get("is_active", 1))),
        )
    for row in (products or []):
        con.execute(
            "INSERT INTO catalog_product "
            "(id, sku, name, slug, category_id, price, cost_price, stock, "
            " ficha_tecnica, is_publishable, quality_score, deleted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row["id"], row["sku"], row["name"], row.get("slug"), row.get("category_id"),
             row.get("price", 0), row.get("cost_price", 0), row.get("stock", 0),
             row.get("ficha_tecnica", ""), int(row.get("is_publishable", 0)),
             row.get("quality_score", 0), row.get("deleted_at")),
        )
    for row in (images or []):
        con.execute(
            "INSERT INTO catalog_productimage (id, product_id, image, position, is_primary, alt_text) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (row["id"], row["product_id"], row["image"],
             row.get("position", 1), int(row.get("is_primary", 0)), row.get("alt_text", "")),
        )
    for row in (compatibilities or []):
        con.execute(
            "INSERT INTO catalog_productcompatibility "
            "(id, product_id, marca, modelo, motor, cilindrada, anio_desde, anio_hasta, combustible) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row["id"], row["product_id"], row.get("marca"), row.get("modelo"),
             row.get("motor"), row.get("cilindrada"), row.get("anio_desde"),
             row.get("anio_hasta"), row.get("combustible")),
        )

    con.commit()
    con.close()
    return db_path


_CATS = [
    {"id": 1, "parent_id": None, "name": "Filtros",        "slug": "filtros"},
    {"id": 2, "parent_id": 1,    "name": "Filtros Aceite",  "slug": "filtros-aceite"},
]
_PRODS = [
    {"id": 1, "sku": "F-001", "name": "Filtro de Aceite", "slug": "filtro-de-aceite",
     "category_id": 2, "price": 4990, "cost_price": 2500, "stock": 10,
     "ficha_tecnica": "Filtro original OEM"},
    {"id": 2, "sku": "F-002", "name": "Filtro de Aire", "slug": "filtro-de-aire",
     "category_id": 1, "price": 3990, "cost_price": 1800, "stock": 5,
     "ficha_tecnica": ""},
]


@pytest.fixture
def empresa(db):
    return EmpresaFactory(nombre_taller="MonteAzul", pais="CL")


@pytest.fixture
def catalog_db(tmp_path):
    return _make_db(tmp_path, categories=_CATS, products=_PRODS)


# ── Fase 2: Categorías ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_imports_categories(empresa, catalog_db):
    from commerce.models import CommerceCategory

    result = MonteAzulAdapter(catalog_db, empresa).run()

    assert result.categories_created == 2
    assert result.errors == []
    assert CommerceCategory.objects.filter(empresa=empresa).count() == 2


@pytest.mark.django_db
def test_category_hierarchy_preserved(empresa, catalog_db):
    from commerce.models import CommerceCategory

    MonteAzulAdapter(catalog_db, empresa).run()

    parent = CommerceCategory.objects.get(empresa=empresa, slug="filtros")
    child = CommerceCategory.objects.get(empresa=empresa, slug="filtros-aceite")
    assert child.parent == parent


@pytest.mark.django_db
def test_category_slug_generated_when_absent(empresa, tmp_path):
    from commerce.models import CommerceCategory

    db = _make_db(tmp_path, categories=[
        {"id": 1, "parent_id": None, "name": "Aceites Motor", "slug": None}
    ])
    MonteAzulAdapter(db, empresa).run()

    assert CommerceCategory.objects.get(empresa=empresa).slug == "aceites-motor"


# ── Fase 3: Productos y Repuestos ─────────────────────────────────────────────

@pytest.mark.django_db
def test_creates_repuesto_and_commerce_product(empresa, catalog_db):
    from commerce.models import CommerceProduct
    from taller.models.repuesto import Repuesto

    result = MonteAzulAdapter(catalog_db, empresa).run()

    assert result.products_created == 2
    assert result.repuestos_created == 2

    rep = Repuesto.objects.get(empresa=empresa, part_number="F-001")
    assert rep.nombre == "Filtro de Aceite"
    assert rep.precio_venta == 4990
    assert rep.precio_compra == 2500
    assert rep.cantidad_stock == 10

    cp = CommerceProduct.objects.get(empresa=empresa, repuesto=rep)
    assert cp.is_publishable is True
    assert cp.descripcion_larga == "Filtro original OEM"
    assert cp.slug == "filtro-de-aceite"


@pytest.mark.django_db
def test_product_category_assigned(empresa, catalog_db):
    from commerce.models import CommerceProduct, CommerceCategory

    MonteAzulAdapter(catalog_db, empresa).run()

    cat = CommerceCategory.objects.get(empresa=empresa, slug="filtros-aceite")
    cp = CommerceProduct.objects.get(empresa=empresa, repuesto__part_number="F-001")
    assert cp.category == cat


@pytest.mark.django_db
def test_deleted_products_skipped(empresa, tmp_path):
    from commerce.models import CommerceProduct

    db = _make_db(tmp_path, categories=_CATS, products=[
        {"id": 1, "sku": "D-001", "name": "Borrado", "price": 100,
         "deleted_at": "2025-01-01T00:00:00"},
        {"id": 2, "sku": "V-001", "name": "Vigente", "price": 200},
    ])
    result = MonteAzulAdapter(db, empresa).run()

    assert result.products_created == 1
    assert CommerceProduct.objects.filter(empresa=empresa).count() == 1
    assert CommerceProduct.objects.get(empresa=empresa).repuesto.part_number == "V-001"


# ── Idempotencia ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_idempotent_reimport(empresa, catalog_db):
    from commerce.models import CommerceCategory, CommerceProduct
    from taller.models.repuesto import Repuesto

    MonteAzulAdapter(catalog_db, empresa).run()
    result2 = MonteAzulAdapter(catalog_db, empresa).run()

    assert result2.categories_created == 0
    assert result2.repuestos_created == 0
    assert result2.products_skipped == 2   # ya existían, overwrite=False
    assert result2.products_created == 0
    assert result2.products_updated == 0

    assert CommerceCategory.objects.filter(empresa=empresa).count() == 2
    assert CommerceProduct.objects.filter(empresa=empresa).count() == 2
    assert Repuesto.objects.filter(empresa=empresa).count() == 2


# ── overwrite ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_overwrite_updates_price_and_cost(empresa, catalog_db):
    from taller.models.repuesto import Repuesto

    MonteAzulAdapter(catalog_db, empresa).run()

    con = sqlite3.connect(str(catalog_db))
    con.execute("UPDATE catalog_product SET price = 9990, cost_price = 5000 WHERE sku = 'F-001'")
    con.commit()
    con.close()

    result = MonteAzulAdapter(catalog_db, empresa, overwrite=True).run()

    assert result.products_updated == 2
    assert result.products_skipped == 0
    rep = Repuesto.objects.get(empresa=empresa, part_number="F-001")
    assert rep.precio_venta == 9990
    assert rep.precio_compra == 5000


@pytest.mark.django_db
def test_overwrite_updates_description(empresa, catalog_db):
    from commerce.models import CommerceProduct

    MonteAzulAdapter(catalog_db, empresa).run()

    con = sqlite3.connect(str(catalog_db))
    con.execute("UPDATE catalog_product SET ficha_tecnica = 'Nueva ficha' WHERE sku = 'F-001'")
    con.commit()
    con.close()

    MonteAzulAdapter(catalog_db, empresa, overwrite=True).run()

    cp = CommerceProduct.objects.get(empresa=empresa, repuesto__part_number="F-001")
    assert cp.descripcion_larga == "Nueva ficha"


# ── dry_run ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dry_run_writes_nothing(empresa, catalog_db):
    from commerce.models import CommerceCategory, CommerceProduct
    from taller.models.repuesto import Repuesto

    result = MonteAzulAdapter(catalog_db, empresa, dry_run=True).run()

    assert result.categories_created == 2
    assert result.products_created == 2
    assert CommerceCategory.objects.filter(empresa=empresa).count() == 0
    assert CommerceProduct.objects.filter(empresa=empresa).count() == 0
    assert Repuesto.objects.filter(empresa=empresa).count() == 0


@pytest.mark.django_db
def test_dry_run_existing_products_count_as_skipped(empresa, catalog_db):
    MonteAzulAdapter(catalog_db, empresa).run()

    result = MonteAzulAdapter(catalog_db, empresa, dry_run=True).run()

    assert result.products_skipped == 2
    assert result.products_created == 0


# ── Imágenes: images_missing vs images_skipped ───────────────────────────────

@pytest.mark.django_db
def test_images_copied_from_media_dir(empresa, tmp_path):
    """Imagen en media/productos/subdir/filtro.jpg → copiada a ProductImage."""
    from commerce.models import CommerceProduct

    media_root = tmp_path / "media"
    img_dir = media_root / "productos" / "2026" / "02"
    img_dir.mkdir(parents=True)
    (img_dir / "filtro.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

    db = _make_db(
        tmp_path,
        categories=_CATS,
        products=_PRODS,
        images=[
            {"id": 1, "product_id": 1, "image": "products/2026/02/filtro.jpg",
             "position": 1, "is_primary": 1, "alt_text": "Filtro"},
        ],
    )
    result = MonteAzulAdapter(db, empresa, media_root=media_root).run()

    assert result.images_copied == 1
    assert result.images_missing == 0
    assert result.images_skipped == 0
    cp = CommerceProduct.objects.get(empresa=empresa, repuesto__part_number="F-001")
    assert cp.images.count() == 1
    assert cp.images.first().is_primary is True


@pytest.mark.django_db
def test_images_missing_when_file_not_on_disk(empresa, catalog_db):
    """images_missing = archivo no encontrado en disco."""
    con = sqlite3.connect(str(catalog_db))
    con.execute(
        "INSERT INTO catalog_productimage VALUES (1, 1, 'products/2026/02/noexiste.jpg', 1, 1, '')"
    )
    con.commit()
    con.close()

    result = MonteAzulAdapter(catalog_db, empresa).run()

    assert result.images_missing == 1
    assert result.images_skipped == 0
    assert result.images_copied == 0


@pytest.mark.django_db
def test_images_skipped_when_product_already_has_images(empresa, tmp_path):
    """images_skipped = producto ya tenía imágenes y overwrite=False."""
    media_root = tmp_path / "media"
    img_dir = media_root / "productos"
    img_dir.mkdir(parents=True)
    (img_dir / "filtro.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

    db = _make_db(
        tmp_path,
        categories=_CATS,
        products=_PRODS,
        images=[
            {"id": 1, "product_id": 1, "image": "products/filtro.jpg",
             "position": 1, "is_primary": 1},
        ],
    )
    # Primera importación: copia la imagen
    MonteAzulAdapter(db, empresa, media_root=media_root).run()

    # Segunda importación sin overwrite: image_rows omitidas (no faltantes)
    result2 = MonteAzulAdapter(db, empresa, media_root=media_root).run()

    assert result2.images_skipped == 1
    assert result2.images_missing == 0
    assert result2.images_copied == 0
    cp_images = __import__("commerce.models.product", fromlist=["ProductImage"]).ProductImage
    assert cp_images.objects.count() == 1  # no se duplicó


@pytest.mark.django_db
def test_overwrite_replaces_images(empresa, tmp_path):
    """overwrite=True borra las imágenes existentes y las reimporta."""
    from commerce.models import CommerceProduct

    media_root = tmp_path / "media" / "productos"
    media_root.mkdir(parents=True)
    (media_root / "filtro.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

    db = _make_db(
        tmp_path,
        categories=_CATS,
        products=_PRODS,
        images=[{"id": 1, "product_id": 1, "image": "products/filtro.jpg", "position": 1, "is_primary": 1}],
    )
    MonteAzulAdapter(db, empresa, media_root=tmp_path / "media").run()
    result2 = MonteAzulAdapter(db, empresa, overwrite=True, media_root=tmp_path / "media").run()

    assert result2.images_copied == 1
    assert result2.images_skipped == 0
    cp = CommerceProduct.objects.get(empresa=empresa, repuesto__part_number="F-001")
    assert cp.images.count() == 1  # reemplazó, no acumuló


# ── --only-* flags ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_only_categories_skips_products(empresa, catalog_db):
    from commerce.models import CommerceCategory, CommerceProduct

    result = MonteAzulAdapter(catalog_db, empresa, only_categories=True).run()

    assert result.categories_created == 2
    assert result.products_created == 0
    assert CommerceCategory.objects.filter(empresa=empresa).count() == 2
    assert CommerceProduct.objects.filter(empresa=empresa).count() == 0


@pytest.mark.django_db
def test_only_products_uses_existing_categories(empresa, catalog_db):
    from commerce.models import CommerceProduct

    MonteAzulAdapter(catalog_db, empresa, only_categories=True).run()

    result = MonteAzulAdapter(catalog_db, empresa, only_products=True).run()

    assert result.products_created == 2
    assert CommerceProduct.objects.filter(empresa=empresa).count() == 2
    cp = CommerceProduct.objects.get(empresa=empresa, repuesto__part_number="F-001")
    assert cp.category is not None


# ── Fase 5: Compatibilidades (stub) ──────────────────────────────────────────

@pytest.mark.django_db
def test_compatibilities_counted_but_not_imported(empresa, tmp_path):
    from taller.models import InterchangePieza

    db = _make_db(
        tmp_path,
        categories=_CATS,
        products=_PRODS,
        compatibilities=[
            {"id": 1, "product_id": 1, "marca": "Toyota", "modelo": "Corolla",
             "anio_desde": 2015, "anio_hasta": 2020, "combustible": "Gasolina"},
            {"id": 2, "product_id": 1, "marca": "Honda", "modelo": "Civic",
             "anio_desde": 2016, "anio_hasta": 2021, "combustible": "Gasolina"},
        ],
    )
    result = MonteAzulAdapter(db, empresa).run()

    assert result.compatibilities_pending == 2
    assert InterchangePieza.objects.filter(empresa=empresa).count() == 0


# ── Errores y casos extremos ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_missing_db_raises_file_not_found(empresa, tmp_path):
    with pytest.raises(FileNotFoundError):
        MonteAzulAdapter(tmp_path / "noexiste.sqlite3", empresa).run()


@pytest.mark.django_db
def test_missing_table_raises_value_error(empresa, tmp_path):
    db_path = tmp_path / "empty.sqlite3"
    sqlite3.connect(str(db_path)).close()

    with pytest.raises(ValueError, match="catalog_category"):
        MonteAzulAdapter(db_path, empresa).run()


@pytest.mark.django_db
def test_product_without_sku_is_skipped(empresa, tmp_path):
    from commerce.models import CommerceProduct

    db = _make_db(tmp_path, categories=_CATS, products=[
        {"id": 1, "sku": "",      "name": "Sin SKU",  "price": 100},
        {"id": 2, "sku": "V-001", "name": "Con SKU",  "price": 200},
    ])
    result = MonteAzulAdapter(db, empresa).run()

    assert result.errors and "SKU" in result.errors[0]
    assert CommerceProduct.objects.filter(empresa=empresa).count() == 1


# ── Reutilización: subclase con esquema diferente ─────────────────────────────

@pytest.mark.django_db
def test_subclass_overrides_table_and_column_names(empresa, tmp_path):
    """
    Verifica que sobreescribir TABLE_* / COL_* es suficiente para adaptar
    el importador a un esquema SQLite de otro cliente.
    """
    from commerce.models import CommerceProduct

    # BD con nombres de tabla/columna completamente distintos
    db_path = tmp_path / "otro_cliente.sqlite3"
    con = sqlite3.connect(str(db_path))
    con.executescript("""
        CREATE TABLE my_categories (
            id INTEGER PRIMARY KEY, parent_id INTEGER,
            name TEXT, slug TEXT, description TEXT, is_active INTEGER DEFAULT 1
        );
        CREATE TABLE my_products (
            id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, title TEXT,
            url_slug TEXT, cat_id INTEGER,
            sell_price REAL DEFAULT 0, buy_price REAL DEFAULT 0, qty INTEGER DEFAULT 0,
            long_desc TEXT DEFAULT '', removed_at TEXT
        );
        CREATE TABLE my_images (
            id INTEGER PRIMARY KEY, prod_id INTEGER, filepath TEXT,
            pos INTEGER DEFAULT 1, primary_flag INTEGER DEFAULT 0, caption TEXT DEFAULT ''
        );
    """)
    con.execute("INSERT INTO my_categories VALUES (1, NULL, 'Motores', 'motores', '', 1)")
    con.execute("INSERT INTO my_products VALUES (1, 'M-100', 'Motor V6', 'motor-v6', 1, 99000, 50000, 3, 'Motor potente', NULL)")
    con.commit()
    con.close()

    class OtroClienteImporter(CatalogImporter):
        TABLE_CATEGORIES = "my_categories"
        TABLE_PRODUCTS = "my_products"
        TABLE_IMAGES = "my_images"
        TABLE_COMPAT = "my_compat_nonexistent"

        COL_SKU = "code"
        COL_NAME = "title"
        COL_SLUG = "url_slug"
        COL_CATEGORY_ID = "cat_id"
        COL_PRICE = "sell_price"
        COL_COST = "buy_price"
        COL_STOCK = "qty"
        COL_DESCRIPTION = "long_desc"
        COL_DELETED_AT = "removed_at"

        COL_IMG_FILE = "filepath"
        COL_IMG_POSITION = "pos"
        COL_IMG_PRIMARY = "primary_flag"
        COL_IMG_ALT = "caption"

        IMAGE_SEARCH_DIRS = ("imagenes",)

    result = OtroClienteImporter(db_path, empresa).run()

    assert result.categories_created == 1
    assert result.products_created == 1
    assert result.repuestos_created == 1
    assert result.errors == []

    cp = CommerceProduct.objects.get(empresa=empresa, repuesto__part_number="M-100")
    assert cp.repuesto.precio_venta == 99000
    assert cp.category.slug == "motores"


# ── manual_review.json ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_manual_review_generated_when_images_missing(empresa, catalog_db, tmp_path):
    """Imágenes faltantes → manual_review.json escrito junto al SQLite."""
    con = sqlite3.connect(str(catalog_db))
    con.execute(
        "INSERT INTO catalog_productimage VALUES (1, 1, 'products/noexiste.jpg', 1, 1, '')"
    )
    con.commit()
    con.close()

    result = MonteAzulAdapter(catalog_db, empresa).run()

    assert result.review_written_to is not None
    assert result.review_written_to.exists()
    import json
    data = json.loads(result.review_written_to.read_text())
    assert data["empresa_id"] == empresa.pk
    assert data["summary"]["missing"] >= 1


@pytest.mark.django_db
def test_manual_review_uses_custom_review_output(empresa, catalog_db, tmp_path):
    """--review-output sobreescribe la ruta por defecto."""
    custom = tmp_path / "custom_review.json"

    con = sqlite3.connect(str(catalog_db))
    con.execute(
        "INSERT INTO catalog_productimage VALUES (1, 1, 'products/noexiste.jpg', 1, 1, '')"
    )
    con.commit()
    con.close()

    result = MonteAzulAdapter(
        catalog_db, empresa, review_output=custom
    ).run()

    assert result.review_written_to == custom
    assert custom.exists()


@pytest.mark.django_db
def test_manual_review_not_generated_when_all_images_found(empresa, tmp_path):
    """Todas las imágenes encontradas → no se genera manual_review.json."""
    media_root = tmp_path / "media"
    img_dir = media_root / "productos"
    img_dir.mkdir(parents=True)
    (img_dir / "filtro.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

    db = _make_db(
        tmp_path,
        categories=_CATS,
        products=_PRODS,
        images=[{"id": 1, "product_id": 1, "image": "products/filtro.jpg", "position": 1, "is_primary": 1}],
    )
    result = MonteAzulAdapter(db, empresa, media_root=media_root).run()

    assert result.review_written_to is None
    assert not (tmp_path / "manual_review.json").exists()


@pytest.mark.django_db
def test_manual_review_not_generated_in_dry_run(empresa, catalog_db, tmp_path):
    """dry_run=True nunca escribe manual_review.json."""
    con = sqlite3.connect(str(catalog_db))
    con.execute(
        "INSERT INTO catalog_productimage VALUES (1, 1, 'products/noexiste.jpg', 1, 1, '')"
    )
    con.commit()
    con.close()

    result = MonteAzulAdapter(catalog_db, empresa, dry_run=True).run()

    assert result.review_written_to is None


@pytest.mark.django_db
def test_manual_review_includes_ambiguous_when_duplicate_filenames(empresa, tmp_path):
    """Mismo nombre de archivo en dos rutas → marcado como ambiguo en manual_review.json."""
    media_root = tmp_path / "media"
    (media_root / "productos" / "a").mkdir(parents=True)
    (media_root / "productos" / "b").mkdir(parents=True)
    # Mismo nombre, dos directorios distintos → ambiguo
    (media_root / "productos" / "a" / "filtro.jpg").write_bytes(b"\xff" * 10)
    (media_root / "productos" / "b" / "filtro.jpg").write_bytes(b"\xff" * 10)

    db = _make_db(
        tmp_path,
        categories=_CATS,
        products=_PRODS,
        images=[{"id": 1, "product_id": 1, "image": "products/filtro.jpg", "position": 1, "is_primary": 1}],
    )
    result = MonteAzulAdapter(db, empresa, media_root=media_root).run()

    assert result.review_written_to is not None
    import json
    data = json.loads(result.review_written_to.read_text())
    assert data["summary"]["ambiguous"] == 1
    assert len(data["ambiguous"][0]["candidates"]) == 2


# ── Aislamiento multi-tenant ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_tenant_isolation(catalog_db):
    from commerce.models import CommerceProduct

    empresa_a = EmpresaFactory(nombre_taller="Empresa A", pais="CL")
    empresa_b = EmpresaFactory(nombre_taller="Empresa B", pais="CL")

    MonteAzulAdapter(catalog_db, empresa_a).run()
    MonteAzulAdapter(catalog_db, empresa_b).run()

    assert CommerceProduct.objects.filter(empresa=empresa_a).count() == 2
    assert CommerceProduct.objects.filter(empresa=empresa_b).count() == 2
