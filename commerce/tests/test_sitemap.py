"""
Tests for commerce_sitemap_xml — multi-tenant Commerce sitemap.

Coverage:
40. Valid tenant → 200 XML with home, categories, products.
41. Unknown host (no empresa) → 404.
42. URLs use request host, not egarage.cl.
43. Inactive categories excluded.
44. Non-publishable products excluded.
45. Empty catalog (no categories/products) → XML with home only.
"""
import pytest
from django.test import Client, RequestFactory, override_settings

from commerce.tests.conftest import make_category, make_product
from commerce.views.sitemap import commerce_sitemap_xml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HOST = "teststore.local"


def _client(empresa):
    with override_settings(COMMERCE_TENANT_MAP={HOST: empresa.pk}):
        yield Client(HTTP_HOST=HOST)


def _get(empresa, path="/commerce/sitemap.xml"):
    with override_settings(COMMERCE_TENANT_MAP={HOST: empresa.pk}):
        return Client(HTTP_HOST=HOST).get(path)


# ---------------------------------------------------------------------------
# 40. Valid tenant — basic response
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_returns_xml(empresa):
    resp = _get(empresa)
    assert resp.status_code == 200
    assert "application/xml" in resp["Content-Type"]
    content = resp.content.decode()
    assert content.startswith("<?xml")
    assert "<urlset" in content


@pytest.mark.django_db
def test_sitemap_contains_home(empresa):
    content = _get(empresa).content.decode()
    assert "/commerce/" in content


@pytest.mark.django_db
def test_sitemap_contains_active_category(empresa):
    make_category(empresa, "Filtros", slug="filtros-sitemap")
    content = _get(empresa).content.decode()
    assert "/commerce/categoria/filtros-sitemap/" in content


@pytest.mark.django_db
def test_sitemap_contains_publishable_product(empresa):
    cat = make_category(empresa, "Filtros", slug="filtros-prod")
    p = make_product(empresa, category=cat, publishable=True)
    content = _get(empresa).content.decode()
    assert f"/commerce/p/{p.slug}/" in content


# ---------------------------------------------------------------------------
# 41. No empresa → 404
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_unknown_host_returns_404():
    resp = Client(HTTP_HOST="unknown.host").get("/commerce/sitemap.xml")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 42. URLs use request host
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_uses_request_host_not_egarage(empresa):
    content = _get(empresa).content.decode()
    assert "egarage.cl" not in content
    assert HOST in content


# ---------------------------------------------------------------------------
# 43. Inactive categories excluded
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_excludes_inactive_category(empresa):
    active = make_category(empresa, "Activa", slug="activa-sm")
    inactive = make_category(empresa, "Inactiva", slug="inactiva-sm")
    inactive.is_active = False
    inactive.save()
    content = _get(empresa).content.decode()
    assert "/commerce/categoria/activa-sm/" in content
    assert "/commerce/categoria/inactiva-sm/" not in content


# ---------------------------------------------------------------------------
# 44. Non-publishable products excluded
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_excludes_non_publishable_product(empresa):
    cat = make_category(empresa, "Cat", slug="cat-pub")
    pub = make_product(empresa, category=cat, publishable=True)
    hidden = make_product(empresa, category=cat, publishable=False)
    content = _get(empresa).content.decode()
    assert f"/commerce/p/{pub.slug}/" in content
    assert f"/commerce/p/{hidden.slug}/" not in content


# ---------------------------------------------------------------------------
# 45. Empty catalog
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_empty_catalog_has_home_only(empresa):
    content = _get(empresa).content.decode()
    assert "/commerce/" in content
    assert "<loc>" in content
    loc_count = content.count("<loc>")
    assert loc_count == 1
