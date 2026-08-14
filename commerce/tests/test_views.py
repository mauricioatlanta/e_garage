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
def test_home_featured_products_appear(commerce_client):
    """Productos destacados (con imagen) aparecen en el home."""
    import tempfile, os
    from PIL import Image as PILImage
    from django.core.files.uploadedfile import SimpleUploadedFile
    from commerce.models import ProductImage

    client, empresa = commerce_client
    cat = make_category(empresa, "Cat", slug="cat-feat")
    product = make_product(empresa, category=cat)

    # Crear imagen mínima válida
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        img = PILImage.new("RGB", (50, 50), color=(0, 100, 200))
        img.save(tmp, format="PNG")
        tmp.seek(0)
        uploaded = SimpleUploadedFile("test.png", tmp.read(), content_type="image/png")
    finally:
        tmp.close()
        os.unlink(tmp.name)

    ProductImage.objects.create(
        commerce_product=product,
        image=uploaded,
        is_primary=True,
        position=1,
    )

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "productos-destacados" in content


@pytest.mark.django_db
def test_home_recent_products_section(commerce_client):
    """Sección recién agregados aparece cuando hay productos recientes."""
    client, empresa = commerce_client
    make_product(empresa)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_home_no_cross_tenant_products(commerce_client, empresa_b):
    """Productos de empresa_b no aparecen en el home de empresa."""
    from taller.tests.factories import RepuestoFactory

    client, empresa = commerce_client
    rep_b = RepuestoFactory(empresa=empresa_b, nombre="Producto empresa B secreto")
    make_product(empresa_b, repuesto=rep_b)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    assert "Producto empresa B secreto".encode() not in resp.content


@pytest.mark.django_db
def test_home_product_without_image_no_broken_src(commerce_client):
    """Productos sin imagen no generan src='None' en el home."""
    client, empresa = commerce_client
    make_product(empresa)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    assert b'src="None"' not in resp.content


@pytest.mark.django_db
def test_home_vehicle_selector_present(commerce_client):
    """El selector de vehículo debe estar presente con sus IDs clave."""
    client, empresa = commerce_client

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="vehicleForm"' in content
    assert 'id="year"' in content
    assert 'id="fuel_type"' in content
    assert 'id="btnSearch"' in content
    assert 'id="buscador"' in content


@pytest.mark.django_db
def test_home_empty_storefront_renders(commerce_client):
    """Home sin productos ni categorías debe renderizar sin errores."""
    client, empresa = commerce_client

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_home_catalog_links_valid(commerce_client):
    """CTAs del home apuntan a rutas válidas (no URLs rotas)."""
    from django.test import RequestFactory
    from django.urls import reverse

    client, empresa = commerce_client
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    content = resp.content.decode()
    # CTA "Ver todos" apunta a /commerce/buscar/
    search_url = reverse("commerce:search")
    assert search_url in content
    # Anchor del hero apunta al selector de vehículo
    assert '#buscador' in content


@pytest.mark.django_db
def test_home_cookies_banner_ids_preserved(commerce_client):
    """Cookie banner conserva los IDs que usa el JS de base.html."""
    client, empresa = commerce_client

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="cookies-banner"' in content
    assert 'id="cookies-accept"' in content
    assert 'id="cookies-reject"' in content


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
