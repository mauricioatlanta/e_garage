"""
Tests para SyncCommerceCatalogService:
- normalización canónica de nombres de categoría
- deduplicación cuando el ERP tiene variantes con/sin tilde
- idempotencia del seed
"""
import pytest

from commerce.models import CommerceCategory
from commerce.services.sync import SyncCommerceCatalogService, _canonical_key


# ── Tests unitarios de _canonical_key (sin DB) ──────────────────────────────

def test_canonical_key_strips_accents():
    assert _canonical_key("Eléctrico e iluminación") == _canonical_key("Electrico e iluminacion")


def test_canonical_key_case_insensitive():
    assert _canonical_key("Filtros") == _canonical_key("FILTROS") == _canonical_key("filtros")


def test_canonical_key_collapses_spaces():
    assert _canonical_key("  Filtros  ") == _canonical_key("Filtros")
    assert _canonical_key("Suspensión  y  dirección") == _canonical_key("Suspension y direccion")


def test_canonical_key_different_names_differ():
    assert _canonical_key("Filtros") != _canonical_key("Frenos")


# ── Tests de deduplicación (con DB) ─────────────────────────────────────────

@pytest.mark.django_db
def test_deduplication_creates_single_category_per_canonical_pair(empresa):
    from taller.models.repuesto import CategoriaRepuesto

    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Eléctrico e iluminación")
    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Electrico e iluminacion")

    SyncCommerceCatalogService(empresa).sync_all(publish_with_stock=False)

    cats = CommerceCategory.objects.filter(empresa=empresa)
    assert cats.count() == 1


@pytest.mark.django_db
def test_deduplication_keeps_accented_name(empresa):
    from taller.models.repuesto import CategoriaRepuesto

    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Electrico e iluminacion")
    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Eléctrico e iluminación")

    SyncCommerceCatalogService(empresa).sync_all(publish_with_stock=False)

    cat = CommerceCategory.objects.get(empresa=empresa)
    assert cat.name == "Eléctrico e iluminación"


@pytest.mark.django_db
def test_deduplication_reassigns_products_to_canonical(empresa):
    from taller.models.repuesto import CategoriaRepuesto
    from taller.tests.factories import RepuestoFactory
    from commerce.tests.conftest import make_category, make_product

    # Simular estado previo: dos CommerceCategorys para el mismo concepto
    cat_erp_con = CategoriaRepuesto.objects.create(empresa=empresa, nombre="Suspensión y dirección")
    cat_erp_sin = CategoriaRepuesto.objects.create(empresa=empresa, nombre="Suspension y direccion")
    cc_con = make_category(empresa, "Suspensión y dirección", slug="suspension-y-direccion-con")
    cc_con.categoria_erp = cat_erp_con
    cc_con.save()
    cc_sin = make_category(empresa, "Suspension y direccion", slug="suspension-y-direccion-sin")
    cc_sin.categoria_erp = cat_erp_sin
    cc_sin.save()

    # El repuesto apunta a la categoría ERP duplicada (sin tilde)
    rep = RepuestoFactory(empresa=empresa, categoria=cat_erp_sin)
    from commerce.models import CommerceProduct
    CommerceProduct.objects.create(
        empresa=empresa, repuesto=rep, category=cc_sin,
        slug="rep-test", is_publishable=True, meta_title="t", meta_description="",
    )

    SyncCommerceCatalogService(empresa).sync_all(publish_with_stock=False)

    # Solo debe quedar una categoría (la canónica con tilde)
    cats = CommerceCategory.objects.filter(empresa=empresa)
    assert cats.count() == 1
    # El producto fue reasignado a la canónica via _sync_products + duplicate_erp map
    cp = CommerceProduct.objects.get(empresa=empresa)
    assert cp.category == cats.first()
    assert cp.category.name == "Suspensión y dirección"


@pytest.mark.django_db
def test_seed_is_idempotent(empresa):
    from taller.models.repuesto import CategoriaRepuesto

    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Filtros")
    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Frenos")

    service = SyncCommerceCatalogService(empresa)
    service.sync_all(publish_with_stock=False)
    count_1 = CommerceCategory.objects.filter(empresa=empresa).count()

    service.sync_all(publish_with_stock=False)
    count_2 = CommerceCategory.objects.filter(empresa=empresa).count()

    assert count_1 == count_2 == 2


@pytest.mark.django_db
def test_seed_idempotent_with_duplicate_erp_categories(empresa):
    from taller.models.repuesto import CategoriaRepuesto

    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Eléctrico e iluminación")
    CategoriaRepuesto.objects.create(empresa=empresa, nombre="Electrico e iluminacion")

    service = SyncCommerceCatalogService(empresa)
    service.sync_all(publish_with_stock=False)
    count_1 = CommerceCategory.objects.filter(empresa=empresa).count()

    service.sync_all(publish_with_stock=False)
    count_2 = CommerceCategory.objects.filter(empresa=empresa).count()

    assert count_1 == count_2 == 1
