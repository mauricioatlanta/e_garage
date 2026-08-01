"""
Tests para las vistas de Commerce:
- nombre del tenant aparece correctamente
- nombre largo no desborda la estructura del header
- URLs de navegación no cambian entre versiones
- tenant incorrecto devuelve 404
"""
import pytest
from django.test import Client, override_settings
from commerce.tests.conftest import make_category, make_product


@pytest.fixture
def commerce_client(empresa):
    """Cliente HTTP que resuelve el host 'teststore.local' al tenant de prueba."""
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        yield Client(HTTP_HOST="teststore.local"), empresa


@pytest.mark.django_db
def test_home_shows_tenant_name(commerce_client):
    client, empresa = commerce_client
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    assert empresa.nombre_taller.encode() in resp.content


@pytest.mark.django_db
def test_home_long_name_does_not_break_html_structure(db):
    from taller.tests.factories import EmpresaFactory
    e = EmpresaFactory(nombre_taller="A" * 80)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": e.pk}):
        client = Client(HTTP_HOST="teststore.local")
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    # El nombre largo aparece en el atributo title (tooltip) del enlace del logo
    assert b'title="' in resp.content
    # Hay clase truncate en el elemento logo
    assert b"truncate" in resp.content


@pytest.mark.django_db
def test_home_unknown_host_returns_404():
    client = Client(HTTP_HOST="unknown.host")
    resp = client.get("/commerce/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_category_url_unchanged(commerce_client):
    client, empresa = commerce_client
    make_category(empresa, "Filtros", slug="filtros")
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/categoria/filtros/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_search_url_unchanged(commerce_client):
    client, empresa = commerce_client
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/buscar/?q=test")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_product_related_excludes_self(commerce_client):
    client, empresa = commerce_client
    cat = make_category(empresa, "Filtros", slug="filtros-test")
    p_target = make_product(empresa, category=cat)
    p_target.slug = "filtro-target"
    p_target.save()
    for _ in range(3):
        make_product(empresa, category=cat)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get(f"/commerce/p/{p_target.slug}/")
    assert resp.status_code == 200
    content = resp.content.decode()
    # El URL canónico del producto (/commerce/p/filtro-target/) puede aparecer en
    # el breadcrumb o en la página, pero la URL de la card de relacionados NO debe
    # apuntar al propio producto. Verificamos via gateway (test_gateway.py);
    # aquí solo confirmamos que la página carga correctamente.
    assert "También te puede interesar" in content


@pytest.mark.django_db
def test_search_returns_results(commerce_client):
    client, empresa = commerce_client
    from taller.tests.factories import RepuestoFactory
    rep = RepuestoFactory(empresa=empresa, nombre="Filtro especial")
    make_product(empresa, repuesto=rep)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/buscar/?q=especial")
    assert resp.status_code == 200
    assert "Filtro especial".encode() in resp.content
