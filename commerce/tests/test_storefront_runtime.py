"""
Tests del Brand Engine Runtime (tests 1-10 del spec):
1.  Tenant con settings usa logo y colores propios.
2.  Tenant sin settings usa fallback.
3.  Dos tenants no comparten branding.
4.  Meta title y description aparecen en HTML.
5.  Nombre largo no rompe header.
6.  Fuente no permitida cae a system-ui.
7.  Página pública solo aparece en su tenant.
8.  Página inactiva devuelve 404.
9.  FAQ se ordena por position.
10. FAQ de otra empresa no aparece.
"""
import pytest
from django.test import Client, override_settings

from commerce.models import CommerceFAQ, CommerceStaticPage, CommerceStorefrontSettings
from commerce.services.storefront_service import ALLOWED_FONTS, CommerceStorefrontService
from commerce.tests.conftest import make_category


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sf(empresa):
    return CommerceStorefrontSettings.objects.create(
        empresa=empresa,
        tagline="Tagline de prueba",
        font_primary="Inter",
        primary_color="#123456",
        secondary_color="#654321",
        accent_color="#abcdef",
        seo_title="MonteAzul SEO",
        seo_description="Descripción SEO de prueba.",
        whatsapp_number="+56912345678",
    )


@pytest.fixture
def faq_page(empresa):
    return CommerceStaticPage.objects.create(
        empresa=empresa,
        key="faq",
        slug="preguntas-frecuentes",
        title="Preguntas frecuentes",
        body="",
        is_active=True,
        position=1,
    )


def make_faq(empresa, page, question, position):
    return CommerceFAQ.objects.create(
        empresa=empresa, page=page,
        question=question, answer="Respuesta.",
        position=position, is_active=True,
    )


def commerce_client(empresa):
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        yield Client(HTTP_HOST="teststore.local")


# ── 1. Tenant con settings usa colores propios ────────────────────────────────

@pytest.mark.django_db
def test_resolve_uses_tenant_colors(empresa, sf):
    brand = CommerceStorefrontService.resolve(empresa)
    assert brand["colors"]["primary"] == "#123456"
    assert brand["colors"]["secondary"] == "#654321"
    assert brand["colors"]["accent"] == "#abcdef"


# ── 2. Tenant sin settings usa fallback seguro ────────────────────────────────

@pytest.mark.django_db
def test_resolve_fallback_when_no_settings(empresa):
    brand = CommerceStorefrontService.resolve(empresa)
    assert brand["storefront"] is None
    assert brand["colors"]["primary"] == "#3B82F6"
    assert brand["font_primary"] == "system-ui"
    assert brand["logo_url"] is None


@pytest.mark.django_db
def test_resolve_none_empresa_returns_fallback():
    brand = CommerceStorefrontService.resolve(None)
    assert brand["storefront"] is None
    assert brand["brand_name"] == ""


# ── 3. Dos tenants no comparten branding ──────────────────────────────────────

@pytest.mark.django_db
def test_resolve_tenant_isolation(empresa, empresa_b):
    CommerceStorefrontSettings.objects.create(
        empresa=empresa, primary_color="#111111",
    )
    CommerceStorefrontSettings.objects.create(
        empresa=empresa_b, primary_color="#222222",
    )
    brand_a = CommerceStorefrontService.resolve(empresa)
    brand_b = CommerceStorefrontService.resolve(empresa_b)
    assert brand_a["colors"]["primary"] == "#111111"
    assert brand_b["colors"]["primary"] == "#222222"
    assert brand_a["colors"]["primary"] != brand_b["colors"]["primary"]


# ── 4. Meta title y description aparecen en HTML ─────────────────────────────

@pytest.mark.django_db
def test_meta_title_and_description_in_html(empresa, sf):
    make_category(empresa)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "MonteAzul SEO" in content
    assert "Descripción SEO de prueba." in content


# ── 5. Nombre largo no rompe el header ───────────────────────────────────────

@pytest.mark.django_db
def test_long_brand_name_has_truncate_class(empresa):
    from taller.tests.factories import EmpresaFactory
    e = EmpresaFactory(nombre_taller="A" * 80)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": e.pk}):
        client = Client(HTTP_HOST="teststore.local")
        resp = client.get("/commerce/")
    assert resp.status_code == 200
    assert b'title="' in resp.content
    assert b'egc-header' in resp.content


# ── 6. Fuente no permitida cae a system-ui ───────────────────────────────────

def test_safe_font_rejects_unknown():
    result = CommerceStorefrontService._safe_font("Papyrus")
    assert result == "system-ui"


def test_safe_font_accepts_allowlist():
    for font in ALLOWED_FONTS:
        assert CommerceStorefrontService._safe_font(font) == font


@pytest.mark.django_db
def test_disallowed_font_in_settings_falls_back(empresa):
    CommerceStorefrontSettings.objects.create(empresa=empresa, font_primary="Papyrus")
    brand = CommerceStorefrontService.resolve(empresa)
    assert brand["font_primary"] == "system-ui"


# ── 7. Página estática solo aparece en su tenant ─────────────────────────────

@pytest.mark.django_db
def test_static_page_tenant_isolation(empresa, empresa_b):
    CommerceStaticPage.objects.create(
        empresa=empresa, key="nosotros", slug="nosotros", title="Nosotros A", is_active=True
    )
    CommerceStaticPage.objects.create(
        empresa=empresa_b, key="nosotros", slug="nosotros", title="Nosotros B", is_active=True
    )
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = Client(HTTP_HOST="teststore.local").get("/commerce/page/nosotros/")
    assert resp.status_code == 200
    assert b"Nosotros A" in resp.content
    assert b"Nosotros B" not in resp.content


# ── 8. Página inactiva devuelve 404 ──────────────────────────────────────────

@pytest.mark.django_db
def test_inactive_page_returns_404(empresa):
    CommerceStaticPage.objects.create(
        empresa=empresa, key="nosotros", slug="nosotros", title="Nosotros", is_active=False
    )
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = Client(HTTP_HOST="teststore.local").get("/commerce/page/nosotros/")
    assert resp.status_code == 404


# ── 9. FAQs se ordenan por position ──────────────────────────────────────────

@pytest.mark.django_db
def test_faq_ordered_by_position(empresa, faq_page):
    make_faq(empresa, faq_page, "Tercera", 3)
    make_faq(empresa, faq_page, "Primera", 1)
    make_faq(empresa, faq_page, "Segunda", 2)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = Client(HTTP_HOST="teststore.local").get("/commerce/page/preguntas-frecuentes/")
    assert resp.status_code == 200
    content = resp.content.decode()
    pos_primera = content.index("Primera")
    pos_segunda = content.index("Segunda")
    pos_tercera = content.index("Tercera")
    assert pos_primera < pos_segunda < pos_tercera


# ── 10. FAQ de otra empresa no aparece ───────────────────────────────────────

@pytest.mark.django_db
def test_faq_tenant_isolation(empresa, empresa_b, faq_page):
    make_faq(empresa, faq_page, "FAQ propia", 1)

    page_b = CommerceStaticPage.objects.create(
        empresa=empresa_b, key="faq", slug="preguntas-frecuentes",
        title="FAQ B", is_active=True
    )
    make_faq(empresa_b, page_b, "FAQ ajena", 1)

    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = Client(HTTP_HOST="teststore.local").get("/commerce/page/preguntas-frecuentes/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "FAQ propia" in content
    assert "FAQ ajena" not in content
