"""
Tests for country hub localization.

Ensures each country hub renders its own regional terminology
and does not accidentally inherit Chilean slang.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from taller.country.hub import COUNTRY_HUB
from taller.seo_views import robots_txt, sitemap_xml
from taller.views.landing_views import (
    hub_argentina,
    hub_brasil,
    hub_chile,
    hub_ecuador,
    hub_mexico,
    hub_peru,
    hub_usa_en,
    hub_usa_es,
    hub_venezuela,
)


# ---------------------------------------------------------------------------
# Hub data completeness
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "country_name", "country_code", "language", "flag", "hero_image",
    "workshop_name", "salvage_name", "parts_name",
    "tire_name", "carwash_name", "bodyshop_name", "electric_name",
    "fleet_name", "soon_label",
}


@pytest.mark.parametrize("key", ["cl", "ar", "pe", "mx", "us_en", "us_es", "ec", "uy", "ve", "br"])
def test_hub_has_all_required_keys(key):
    hub = COUNTRY_HUB[key]
    missing = REQUIRED_KEYS - set(hub.keys())
    assert not missing, f"COUNTRY_HUB['{key}'] is missing keys: {missing}"


# ---------------------------------------------------------------------------
# Rendered HTML — correct terminology per country
# ---------------------------------------------------------------------------

@pytest.fixture
def rf():
    return RequestFactory()


def _get_html(view_fn, rf):
    request = rf.get("/")
    request.user = AnonymousUser()
    response = view_fn(request)
    return response.content.decode()


@pytest.mark.django_db
def test_chile_hub_terminology(rf):
    html = _get_html(hub_chile, rf)
    assert "Vulcanización" in html
    assert "Lavado de Autos" in html
    assert "Hojalatería y Pintura" in html
    assert "Electricidad Automotriz" in html
    assert "Flotas" in html


@pytest.mark.django_db
def test_argentina_hub_terminology(rf):
    html = _get_html(hub_argentina, rf)
    assert "Gomería" in html
    assert "Lavadero" in html
    assert "Chapa y Pintura" in html
    assert "Electricidad del Automotor" in html
    assert "Desarmadero" in html


@pytest.mark.django_db
def test_peru_hub_terminology(rf):
    html = _get_html(hub_peru, rf)
    assert "Llantería" in html
    assert "Planchado y Pintura" in html
    assert "Desarmadero" in html


@pytest.mark.django_db
def test_mexico_hub_terminology(rf):
    html = _get_html(hub_mexico, rf)
    assert "Yonke" in html
    assert "Refaccionaria" in html
    assert "Llantera" in html
    assert "Autolavado" in html
    assert "Eléctrico Automotriz" in html
    assert "Flotillas" in html


@pytest.mark.django_db
def test_usa_en_hub_terminology(rf):
    html = _get_html(hub_usa_en, rf)
    assert "Tire Shop" in html
    assert "Car Wash" in html
    assert "Body Shop" in html
    assert "Auto Electrical" in html
    assert "Fleet Management" in html
    assert "Salvage Yard" in html
    assert "Auto Repair Shop" in html


@pytest.mark.django_db
def test_usa_es_hub_terminology(rf):
    html = _get_html(hub_usa_es, rf)
    assert "Llantera" in html
    assert "Lavado de Autos" in html
    assert "Hojalatería y Pintura" in html
    assert "Electricidad Automotriz" in html
    assert "Yonke" in html


# ---------------------------------------------------------------------------
# Cross-contamination checks — Chilean slang must not appear in other hubs
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_no_chilean_slang_in_argentina(rf):
    html = _get_html(hub_argentina, rf)
    assert "Vulcanización" not in html
    assert "Desarmaduría" not in html


@pytest.mark.django_db
def test_no_chilean_slang_in_mexico(rf):
    html = _get_html(hub_mexico, rf)
    assert "Vulcanización" not in html
    assert "Desarmaduría" not in html


@pytest.mark.django_db
def test_no_chilean_slang_in_peru(rf):
    html = _get_html(hub_peru, rf)
    assert "Vulcanización" not in html


@pytest.mark.django_db
def test_no_spanish_in_usa_en(rf):
    html = _get_html(hub_usa_en, rf)
    assert "Vulcanización" not in html
    assert "Gomería" not in html
    assert "Llantera" not in html


@pytest.mark.django_db
def test_no_english_in_usa_es(rf):
    html = _get_html(hub_usa_es, rf)
    assert "Tire Shop" not in html
    assert "Car Wash" not in html
    assert "Fleet Management" not in html


# ---------------------------------------------------------------------------
# Language attribute in <html>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_usa_en_html_lang(rf):
    html = _get_html(hub_usa_en, rf)
    assert 'lang="en"' in html


@pytest.mark.django_db
def test_usa_es_html_lang(rf):
    html = _get_html(hub_usa_es, rf)
    assert 'lang="es"' in html


@pytest.mark.django_db
def test_chile_html_lang(rf):
    html = _get_html(hub_chile, rf)
    assert 'lang="es"' in html


# ---------------------------------------------------------------------------
# Coverage for ec / ve / br hubs (previously untested)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ecuador_hub_terminology(rf):
    html = _get_html(hub_ecuador, rf)
    assert "Llantera" in html
    assert "Chatarrería" in html
    assert "Almacén de Repuestos" in html
    assert "Enderezada y Pintura" in html


@pytest.mark.django_db
def test_venezuela_hub_terminology(rf):
    html = _get_html(hub_venezuela, rf)
    assert "Cauchera" in html
    assert "Desarmadero" in html
    assert "Latonería y Pintura" in html


@pytest.mark.django_db
def test_brasil_hub_terminology(rf):
    html = _get_html(hub_brasil, rf)
    assert "Oficina Mecânica" in html
    assert "Borracharia" in html
    assert "Desmanche" in html
    assert "Funilaria e Pintura" in html
    assert "Frotas" in html


@pytest.mark.django_db
def test_brasil_hub_html_lang(rf):
    html = _get_html(hub_brasil, rf)
    assert 'lang="pt"' in html


@pytest.mark.django_db
def test_no_chilean_slang_in_ecuador(rf):
    html = _get_html(hub_ecuador, rf)
    assert "Vulcanización" not in html


@pytest.mark.django_db
def test_no_spanish_in_brasil(rf):
    html = _get_html(hub_brasil, rf)
    assert "Vulcanización" not in html
    assert "Gomería" not in html


# ---------------------------------------------------------------------------
# Sitemap regression — all country landing URLs must be present
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sitemap_returns_xml(rf):
    request = rf.get("/sitemap.xml")
    request.user = AnonymousUser()
    response = sitemap_xml(request)
    assert response.status_code == 200
    assert "application/xml" in response["Content-Type"]
    content = response.content.decode()
    assert content.startswith("<?xml")
    assert "<urlset" in content


@pytest.mark.django_db
def test_sitemap_contains_all_country_hubs(rf):
    request = rf.get("/sitemap.xml")
    request.user = AnonymousUser()
    content = sitemap_xml(request).content.decode()
    for path in ("/cl/", "/ar/", "/pe/", "/mx/", "/ec/", "/ve/", "/br/", "/uy/es/", "/us/", "/us/en/", "/us/es/"):
        assert path in content, f"Sitemap missing hub path: {path}"


@pytest.mark.django_db
def test_usa_hubs_have_self_canonical_and_hreflang(rf):
    en_html = _get_html(hub_usa_en, rf)
    es_html = _get_html(hub_usa_es, rf)

    assert 'rel="canonical" href="https://egarage.cl/us/en/"' in en_html
    assert 'rel="canonical" href="https://egarage.cl/us/es/"' in es_html

    for html in (en_html, es_html):
        assert 'hreflang="en-US" href="https://egarage.cl/us/en/"' in html
        assert 'hreflang="es-US" href="https://egarage.cl/us/es/"' in html


@pytest.mark.django_db
def test_sitemap_contains_landing_urls(rf):
    request = rf.get("/sitemap.xml")
    request.user = AnonymousUser()
    content = sitemap_xml(request).content.decode()
    # Spot-check key localized landing URLs
    for path in (
        "/cl/talleres/", "/cl/repuestos/", "/cl/vulcanizaciones/",
        "/ar/gomeria/", "/mx/refaccionaria/", "/mx/yonke/",
        "/us/en/auto-repair/", "/us/es/talleres/",
        "/br/oficina-mecanica/", "/br/borracharia/",
        "/ve/cauchera/", "/ec/llantera/",
        "/uy/talleres/", "/uy/casas-de-repuestos/",
        "/uy/desarmadurias/", "/uy/neumaticos/", "/uy/lavado/",
    ):
        assert path in content, f"Sitemap missing landing path: {path}"


@pytest.mark.django_db
def test_sitemap_uses_canonical_host(rf):
    import re
    request = rf.get("/sitemap.xml")
    request.user = AnonymousUser()
    content = sitemap_xml(request).content.decode()
    assert "https://egarage.cl" in content
    # Every <loc> entry must use the HTTPS canonical host (namespace URI is excluded)
    locs = re.findall(r"<loc>(.*?)</loc>", content)
    assert locs, "Sitemap has no <loc> entries"
    for loc in locs:
        assert loc.startswith("https://egarage.cl"), f"Non-canonical loc: {loc}"


@pytest.mark.django_db
def test_uruguay_engine_and_legacy_routes(client):
    public_paths = (
        "/uy/talleres/",
        "/uy/casas-de-repuestos/",
        "/uy/desarmadurias/",
        "/uy/neumaticos/",
        "/uy/lavado/",
    )
    for path in public_paths:
        response = client.get(path, follow=False)
        assert response.status_code == 200, path

    root = client.get("/uy/", follow=False)
    assert root.status_code == 302
    assert root["Location"] == "/uy/es/"

    assert client.get("/uy/es/", follow=False).status_code == 200

    legacy = client.get("/uy/repuestos/", follow=False)
    assert legacy.status_code == 302
    assert "/accounts/login/" in legacy["Location"]

    legacy_es = client.get("/uy/es/repuestos/", follow=False)
    assert legacy_es.status_code == 302
    assert "/accounts/login/" in legacy_es["Location"]


@pytest.mark.django_db
def test_sitemap_contains_complete_uruguay_surface(rf):
    request = rf.get("/sitemap.xml")
    request.user = AnonymousUser()
    content = sitemap_xml(request).content.decode()

    expected = (
        "/uy/es/",
        "/uy/talleres/",
        "/uy/casas-de-repuestos/",
        "/uy/desarmadurias/",
        "/uy/neumaticos/",
        "/uy/lavado/",
    )
    for path in expected:
        assert f"https://egarage.cl{path}" in content

    import re
    locs = re.findall(r"<loc>(.*?)</loc>", content)
    assert len(locs) == 62


# ---------------------------------------------------------------------------
# robots_txt — host-aware sitemap pointer
# ---------------------------------------------------------------------------

@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_robots_txt_egarage_domain_points_to_canonical_sitemap(rf):
    request = rf.get("/robots.txt", HTTP_HOST="egarage.cl")
    request.is_custom_domain = False
    content = robots_txt(request).content.decode()
    assert "Sitemap: https://egarage.cl/sitemap.xml" in content
    assert "commerce/sitemap.xml" not in content


@pytest.mark.django_db
def test_robots_txt_custom_domain_points_to_commerce_sitemap(rf):
    request = rf.get("/robots.txt", HTTP_HOST="www.monteazulspa.cl")
    request.is_custom_domain = True
    content = robots_txt(request).content.decode()
    assert "Sitemap: https://www.monteazulspa.cl/commerce/sitemap.xml" in content
    assert "egarage.cl/sitemap.xml" not in content


@pytest.mark.django_db
def test_robots_txt_custom_domain_uses_request_host(rf):
    request = rf.get("/robots.txt", HTTP_HOST="otro-taller.cl")
    request.is_custom_domain = True
    content = robots_txt(request).content.decode()
    assert "https://otro-taller.cl/commerce/sitemap.xml" in content
