"""
Tests for PARTS 2.0 Sprint 1: repuesto search endpoint + workspace routing.

Covers:
  1.  PARTS profile → workspace_search_url points to repuestos/buscar/
  2.  WORKSHOP profile → workspace_search_url points to workspace/buscar/
  3.  SKU exacto (part_number iexact) aparece primero
  4.  SKU istartswith aparece antes que icontains
  5.  Búsqueda por nombre funciona (icontains)
  6.  Búsqueda por proveedor funciona (icontains)
  7.  No retorna repuestos de otra empresa
  8.  Usuario no autenticado recibe 302
  9.  Query corta (< 2 chars) devuelve vehiculos vacío
  10. Cada resultado contiene title, subtitle, url
  11. La url de cada resultado apunta a /repuestos/<pk>/
  12. Límite máximo de resultados = 10
"""

import json

import pytest
from django.test import Client
from django.urls import reverse

from taller.tests.factories import (
    ConfiguracionEmpresaFactory,
    EmpresaFactory,
    RepuestoFactory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parts_empresa():
    """Returns an Empresa whose rubro_principal is PARTS."""
    empresa = EmpresaFactory(pais="CL", with_config=True)
    config = empresa.config
    config.rubro_principal = "PARTS"
    config.save(update_fields=["rubro_principal"])
    return empresa


def _workshop_empresa():
    """Returns an Empresa whose rubro_principal is WORKSHOP (default)."""
    empresa = EmpresaFactory(pais="CL", with_config=True)
    return empresa


def _search(client, prefix="/cl/es", q="alt"):
    """GET /cl/es/repuestos/buscar/?q=<q> and return parsed JSON."""
    url = f"{prefix}/repuestos/buscar/?q={q}"
    response = client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    return response, json.loads(response.content)


# ---------------------------------------------------------------------------
# 1-2: workspace_search_url routing
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_parts_profile_gets_repuestos_search_url():
    """workspace_dashboard passes /repuestos/buscar/ for PARTS profile."""
    empresa = _parts_empresa()
    c = Client()
    c.force_login(empresa.user)
    response = c.get("/cl/es/workspace/")
    # The URL is consumed by the template, but we can verify via context
    assert response.status_code == 200
    assert "workspace_search_url" in response.context
    assert "/repuestos/buscar/" in response.context["workspace_search_url"]


@pytest.mark.django_db
def test_workshop_profile_gets_workspace_search_url():
    """workspace_dashboard passes /workspace/buscar/ for WORKSHOP profile."""
    empresa = _workshop_empresa()
    c = Client()
    c.force_login(empresa.user)
    response = c.get("/cl/es/workspace/")
    assert response.status_code == 200
    assert "/workspace/buscar/" in response.context["workspace_search_url"]


# ---------------------------------------------------------------------------
# 3-6: search priority and field coverage
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_exact_part_number_appears_first():
    """SKU exacto debe aparecer en posición 0."""
    empresa = _parts_empresa()
    RepuestoFactory(empresa=empresa, nombre="Alternador genérico", part_number="ALT-999X")
    target = RepuestoFactory(empresa=empresa, nombre="Alternador Toyota", part_number="ALT-001")
    RepuestoFactory(empresa=empresa, nombre="Alternador Corolla", part_number="XALT-001")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="ALT-001")

    vehiculos = data["vehiculos"]
    assert len(vehiculos) > 0
    assert vehiculos[0]["id"] == target.pk


@pytest.mark.django_db
def test_part_number_istartswith_before_icontains():
    """PN que empieza con query aparece antes que PN que solo contiene query."""
    empresa = _parts_empresa()
    # Only icontains match
    fuzzy = RepuestoFactory(empresa=empresa, nombre="Pieza X", part_number="X-ALT-200")
    # istartswith match
    prefix = RepuestoFactory(empresa=empresa, nombre="Pieza Y", part_number="ALT-200")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="ALT-2")

    pks = [v["id"] for v in data["vehiculos"]]
    assert prefix.pk in pks
    assert fuzzy.pk in pks
    assert pks.index(prefix.pk) < pks.index(fuzzy.pk)


@pytest.mark.django_db
def test_search_by_nombre_icontains():
    """Nombre icontains returns matching repuesto."""
    empresa = _parts_empresa()
    rep = RepuestoFactory(empresa=empresa, nombre="Filtro de aceite Bosch")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="aceite")

    pks = [v["id"] for v in data["vehiculos"]]
    assert rep.pk in pks


@pytest.mark.django_db
def test_search_by_proveedor_icontains():
    """Proveedor icontains returns matching repuesto."""
    empresa = _parts_empresa()
    rep = RepuestoFactory(empresa=empresa, nombre="Pieza X", proveedor="Distribuidora AutoMax")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="automax")

    pks = [v["id"] for v in data["vehiculos"]]
    assert rep.pk in pks


# ---------------------------------------------------------------------------
# 7: multi-tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_no_cross_tenant_results():
    """Results must never include repuestos from another empresa."""
    empresa_a = _parts_empresa()
    empresa_b = _parts_empresa()

    RepuestoFactory(empresa=empresa_b, nombre="Repuesto secreto B", part_number="SEC-001")
    RepuestoFactory(empresa=empresa_a, nombre="Repuesto A", part_number="PUB-001")

    c = Client()
    c.force_login(empresa_a.user)
    _, data = _search(c, q="SEC")

    assert data["vehiculos"] == []


# ---------------------------------------------------------------------------
# 8: authentication
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_unauthenticated_gets_redirect():
    """Unauthenticated request should be redirected (302)."""
    empresa = _parts_empresa()
    RepuestoFactory(empresa=empresa, nombre="Test")
    c = Client()
    response = c.get("/cl/es/repuestos/buscar/?q=test")
    assert response.status_code in (302, 301)


# ---------------------------------------------------------------------------
# 9: short query returns empty
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_short_query_returns_empty():
    """Query shorter than 2 chars returns empty vehiculos list."""
    empresa = _parts_empresa()
    RepuestoFactory(empresa=empresa, nombre="Alternador")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="A")

    assert data["vehiculos"] == []
    assert data["meta"]["min_chars"] == 2


@pytest.mark.django_db
def test_empty_query_returns_empty():
    """Empty query returns empty vehiculos list."""
    empresa = _parts_empresa()
    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="")

    assert data["vehiculos"] == []


# ---------------------------------------------------------------------------
# 10-11: JSON contract
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_result_has_required_keys():
    """Each result must have title, subtitle, and url."""
    empresa = _parts_empresa()
    RepuestoFactory(empresa=empresa, nombre="Bujía NGK", part_number="BUJ-001", cantidad_stock=3)

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="BUJ")

    assert len(data["vehiculos"]) >= 1
    item = data["vehiculos"][0]
    assert "title" in item
    assert "subtitle" in item
    assert "url" in item


@pytest.mark.django_db
def test_result_url_points_to_detail():
    """Each result url must contain /repuestos/<pk>/."""
    empresa = _parts_empresa()
    rep = RepuestoFactory(empresa=empresa, nombre="Correa dentada", part_number="CD-500")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="CD-500")

    assert len(data["vehiculos"]) >= 1
    item = data["vehiculos"][0]
    assert f"/repuestos/{rep.pk}/" in item["url"]


@pytest.mark.django_db
def test_subtitle_includes_part_number_and_stock():
    """Subtitle should contain PN and stock info."""
    empresa = _parts_empresa()
    RepuestoFactory(empresa=empresa, nombre="Amortiguador", part_number="AMO-123", cantidad_stock=7)

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="AMO-123")

    item = data["vehiculos"][0]
    assert "AMO-123" in item["subtitle"]
    assert "7" in item["subtitle"]


# ---------------------------------------------------------------------------
# 12: result limit
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_result_limit_is_ten():
    """Endpoint must never return more than 10 results."""
    empresa = _parts_empresa()
    for i in range(15):
        RepuestoFactory(empresa=empresa, nombre=f"Repuesto Filtro {i}", part_number=f"FIL-{i:03d}")

    c = Client()
    c.force_login(empresa.user)
    _, data = _search(c, q="Filtro")

    assert len(data["vehiculos"]) <= 10
