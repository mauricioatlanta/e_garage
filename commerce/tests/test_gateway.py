"""
Tests para CommerceCatalogGateway:
- exclude_product excluye el producto actual de los relacionados
- aislamiento multi-tenant
"""
import pytest
from taller.tests.factories import RepuestoFactory
from commerce.services.gateway import CommerceCatalogGateway
from commerce.tests.conftest import make_category, make_product


@pytest.mark.django_db
def test_list_products_excludes_given_product(empresa):
    cat = make_category(empresa)
    p1 = make_product(empresa, category=cat)
    p2 = make_product(empresa, category=cat)
    p3 = make_product(empresa, category=cat)

    gw = CommerceCatalogGateway(empresa)
    result = list(gw.list_products(category=cat, exclude_product=p1))

    assert p1 not in result
    assert p2 in result
    assert p3 in result


@pytest.mark.django_db
def test_list_products_without_exclude_returns_all(empresa):
    cat = make_category(empresa)
    p1 = make_product(empresa, category=cat)
    p2 = make_product(empresa, category=cat)

    gw = CommerceCatalogGateway(empresa)
    result = list(gw.list_products(category=cat))

    assert p1 in result
    assert p2 in result


@pytest.mark.django_db
def test_list_products_limit_applied_after_exclude(empresa):
    cat = make_category(empresa)
    products = [make_product(empresa, category=cat) for _ in range(6)]

    gw = CommerceCatalogGateway(empresa)
    result = list(gw.list_products(category=cat, limit=4, exclude_product=products[0]))

    assert len(result) == 4
    assert products[0] not in result


@pytest.mark.django_db
def test_gateway_tenant_isolation(empresa, empresa_b):
    cat_a = make_category(empresa, "Filtros A")
    cat_b = make_category(empresa_b, "Filtros B")
    p_a = make_product(empresa, category=cat_a)
    p_b = make_product(empresa_b, category=cat_b)

    gw_a = CommerceCatalogGateway(empresa)
    results_a = list(gw_a.list_products())

    assert p_a in results_a
    assert p_b not in results_a


@pytest.mark.django_db
def test_gateway_only_returns_publishable(empresa):
    cat = make_category(empresa)
    pub = make_product(empresa, category=cat, publishable=True)
    hidden = make_product(empresa, category=cat, publishable=False)

    gw = CommerceCatalogGateway(empresa)
    result = list(gw.list_products())

    assert pub in result
    assert hidden not in result


@pytest.mark.django_db
def test_get_categories_tenant_isolation(empresa, empresa_b):
    make_category(empresa, "Cat A")
    make_category(empresa_b, "Cat B")

    gw_a = CommerceCatalogGateway(empresa)
    cats_a = list(gw_a.get_categories())

    names = [c.name for c in cats_a]
    assert "Cat A" in names
    assert "Cat B" not in names
