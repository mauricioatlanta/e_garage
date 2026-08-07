"""
Tests for country hub localization.

Ensures each country hub renders its own regional terminology
and does not accidentally inherit Chilean slang.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from taller.country.hub import COUNTRY_HUB
from taller.views.landing_views import (
    hub_argentina,
    hub_chile,
    hub_mexico,
    hub_peru,
    hub_usa_en,
    hub_usa_es,
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


@pytest.mark.parametrize("key", ["cl", "ar", "pe", "mx", "us_en", "us_es"])
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
