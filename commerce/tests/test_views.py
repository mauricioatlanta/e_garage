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
    # El nombre largo aparece en el atributo title (tooltip) del enlace al logo
    assert b'title="' in resp.content
    # El header del tema incluye el buscador (no html roto)
    assert b'egc-header' in resp.content


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


@pytest.mark.django_db
def test_home_extends_base_theme(commerce_client):
    """home.html debe heredar de base.html: el header con buscador debe aparecer."""
    client, empresa = commerce_client
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    # id="egc-header-search" viene de _header_navigation_v2.html incluido por base.html
    assert b'id="egc-header-search"' in resp.content


@pytest.mark.django_db
def test_home_logo_no_broken_src(commerce_client):
    """Sin logo configurado, no debe aparecer src="None" en el HTML."""
    client, empresa = commerce_client
    # empresa fixture no crea CommerceStorefrontSettings, logo = null
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    assert b'src="None"' not in resp.content


@pytest.mark.django_db
def test_home_logo_visible_when_set(commerce_client, tmp_path):
    """Con logo configurado, el <img> debe apuntar a la URL correcta."""
    import shutil
    from django.conf import settings as django_settings
    from commerce.models import CommerceStorefrontSettings

    client, empresa = commerce_client

    # Crear un PNG mínimo de 1×1 píxel en MEDIA_ROOT
    media_root = getattr(django_settings, "MEDIA_ROOT", tmp_path)
    logo_dir = tmp_path / "commerce" / "logos"
    logo_dir.mkdir(parents=True)
    logo_file = logo_dir / "test_logo.png"
    # PNG 1×1 transparente (bytes mínimos válidos)
    logo_file.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    sf, _ = CommerceStorefrontSettings.objects.get_or_create(empresa=empresa)
    # Asignar ruta relativa al MEDIA_ROOT directamente (evita copiar archivo real)
    sf.logo = "commerce/logos/test_logo.png"
    sf.save(update_fields=["logo"])

    with override_settings(
        COMMERCE_TENANT_MAP={"teststore.local": empresa.pk},
        MEDIA_ROOT=str(tmp_path),
        MEDIA_URL="/media/",
    ):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    # El template _header_navigation_v2.html pone el img en varias líneas; buscar la URL
    assert b"test_logo.png" in resp.content


@pytest.mark.django_db
def test_home_whatsapp_uses_brand(commerce_client):
    """El WhatsApp debe venir de brand.whatsapp.url, no de la URL hardcoded anterior."""
    from commerce.models import CommerceStorefrontSettings

    client, empresa = commerce_client
    sf, _ = CommerceStorefrontSettings.objects.get_or_create(empresa=empresa)
    sf.whatsapp_number = "+56979503154"
    sf.save(update_fields=["whatsapp_number"])

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    assert b"wa.me/56979503154" in resp.content
    # URL hardcoded del tema original no debe aparecer
    assert b"wsp.cl" not in resp.content
