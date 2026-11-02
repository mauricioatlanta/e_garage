"""
Tests for Welcome Experience 2.0 / 2.1 pages.

Coverage:
- welcome_config: all 11 country configs have the required fields (Sprint A)
- bienvenida views: HTTP 200, CSS vars, terminology pills, social_proof, market_insight
- get_config: fallback behaviour for unknown (country, lang) pairs

Runner: pytest (see pytest.ini — DJANGO_SETTINGS_MODULE=gestion_taller.settings_test)
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from taller.welcome_config import WELCOME_CONFIG, HERO_RUBRO_SCENES, DASHBOARD_SCENE, get_config
from taller.views_extra.bienvenida import (
    bienvenida_ar,
    bienvenida_br_pt,
    bienvenida_co,
    bienvenida_ec,
    bienvenida_mx,
    bienvenida_pe,
    bienvenida_uy,
    bienvenida_us_en,
    bienvenida_us_es,
    bienvenida_ve,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED_SPRINT_A_FIELDS = [
    "theme",
    "art_direction",
    "cities",
    "vehicles",
    "priority_rubro",
    "market_insight",
    "social_proof",
]

_REQUIRED_THEME_KEYS = {"primary", "accent", "badge"}
_REQUIRED_INSIGHT_KEYS = {"headline", "tip", "focus"}


def _get(view_fn, path):
    factory = RequestFactory()
    req = factory.get(path)
    req.user = AnonymousUser()
    return view_fn(req)


# ---------------------------------------------------------------------------
# Config unit tests — no DB, no HTTP
# ---------------------------------------------------------------------------

ALL_COUNTRY_KEYS = list(WELCOME_CONFIG.keys())


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_has_sprint_a_fields(key):
    cfg = WELCOME_CONFIG[key]
    for field in _REQUIRED_SPRINT_A_FIELDS:
        assert field in cfg, f"({key}): missing '{field}'"


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_theme_has_all_keys(key):
    theme = WELCOME_CONFIG[key]["theme"]
    assert _REQUIRED_THEME_KEYS <= set(theme.keys()), f"({key}): theme missing keys"
    for k, v in theme.items():
        assert v.startswith("#"), f"({key}): theme.{k} must be a hex color, got {v!r}"


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_market_insight_has_all_keys(key):
    insight = WELCOME_CONFIG[key]["market_insight"]
    assert _REQUIRED_INSIGHT_KEYS <= set(insight.keys()), f"({key}): market_insight missing keys"
    for k in _REQUIRED_INSIGHT_KEYS:
        assert insight[k], f"({key}): market_insight.{k} is empty"


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_social_proof_has_stats(key):
    sp = WELCOME_CONFIG[key]["social_proof"]
    assert "stats" in sp, f"({key}): social_proof missing 'stats'"
    assert len(sp["stats"]) >= 2, f"({key}): social_proof.stats must have at least 2 items"
    for stat in sp["stats"]:
        assert "value" in stat and "label" in stat, f"({key}): stat item missing 'value' or 'label'"


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_vehicles_nonempty(key):
    vehicles = WELCOME_CONFIG[key]["vehicles"]
    assert isinstance(vehicles, list) and len(vehicles) >= 3, f"({key}): need at least 3 vehicles"


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_terminology_has_three_terms(key):
    terms = WELCOME_CONFIG[key].get("terminology", [])
    assert len(terms) == 3, f"({key}): expected 3 terminology items, got {len(terms)}"
    for t in terms:
        assert "label" in t and "value" in t, f"({key}): term missing 'label' or 'value'"


_REQUIRED_ART_KEYS = {"lighting", "camera", "mood", "environment", "people", "dashboard"}


@pytest.mark.parametrize("key", ALL_COUNTRY_KEYS, ids=[f"{c}-{l}" for c, l in ALL_COUNTRY_KEYS])
def test_config_art_direction_has_all_keys(key):
    art = WELCOME_CONFIG[key]["art_direction"]
    assert _REQUIRED_ART_KEYS <= set(art.keys()), f"({key}): art_direction missing keys"
    assert art["people"] is True, f"({key}): art_direction.people must be True (personas are protagonists)"
    assert art["dashboard"].startswith("marketing"), f"({key}): art_direction.dashboard must start with 'marketing'"


_REQUIRED_SCENE_KEYS = {
    "scene", "rubro", "label", "description", "image",
    "camera", "lighting", "mood",
    "people", "people_roles", "people_action",
    "vehicle", "composition", "overlay", "dashboard",
}

_REQUIRED_DASHBOARD_KEYS = (_REQUIRED_SCENE_KEYS - {"rubro"}) | {"kpis"}


# ---------------------------------------------------------------------------
# HERO_RUBRO_SCENES unit tests — no DB, no HTTP
# ---------------------------------------------------------------------------

def test_hero_rubro_scenes_count():
    assert len(HERO_RUBRO_SCENES) == 4


@pytest.mark.parametrize("scene", HERO_RUBRO_SCENES, ids=[s["scene"] for s in HERO_RUBRO_SCENES])
def test_rubro_scene_has_all_keys(scene):
    assert _REQUIRED_SCENE_KEYS <= set(scene.keys()), f"scene '{scene['scene']}' missing keys"


@pytest.mark.parametrize("scene", HERO_RUBRO_SCENES, ids=[s["scene"] for s in HERO_RUBRO_SCENES])
def test_rubro_scene_people_is_true(scene):
    assert scene["people"] is True, f"scene '{scene['scene']}': people must be True — personas are protagonists"


@pytest.mark.parametrize("scene", HERO_RUBRO_SCENES, ids=[s["scene"] for s in HERO_RUBRO_SCENES])
def test_rubro_scene_dashboard_is_false(scene):
    assert scene["dashboard"] is False, f"scene '{scene['scene']}': dashboard must be False for rubro scenes"


@pytest.mark.parametrize("scene", HERO_RUBRO_SCENES, ids=[s["scene"] for s in HERO_RUBRO_SCENES])
def test_rubro_scene_people_action_nonempty(scene):
    assert scene["people_action"], f"scene '{scene['scene']}': people_action must not be empty"


@pytest.mark.parametrize("scene", HERO_RUBRO_SCENES, ids=[s["scene"] for s in HERO_RUBRO_SCENES])
def test_rubro_scene_people_roles_nonempty(scene):
    assert scene["people_roles"], f"scene '{scene['scene']}': people_roles must have at least one entry"


@pytest.mark.parametrize("scene", HERO_RUBRO_SCENES, ids=[s["scene"] for s in HERO_RUBRO_SCENES])
def test_rubro_scene_image_path(scene):
    assert scene["image"].startswith("img/welcome/scenes/"), f"scene '{scene['scene']}': unexpected image path"
    assert scene["image"].endswith(".webp"), f"scene '{scene['scene']}': image must be .webp"


# ---------------------------------------------------------------------------
# DASHBOARD_SCENE unit tests
# ---------------------------------------------------------------------------

def test_dashboard_scene_has_all_keys():
    assert _REQUIRED_DASHBOARD_KEYS <= set(DASHBOARD_SCENE.keys())


def test_dashboard_scene_dashboard_is_true():
    assert DASHBOARD_SCENE["dashboard"] is True


def test_dashboard_scene_people_is_false():
    assert DASHBOARD_SCENE["people"] is False


def test_dashboard_scene_kpis_nonempty():
    assert len(DASHBOARD_SCENE["kpis"]) >= 3


# ---------------------------------------------------------------------------
# get_config global-injection tests
# ---------------------------------------------------------------------------

def test_get_config_injects_global_constants():
    cfg = get_config("mx", "es")
    assert "platform_stats" in cfg
    assert len(cfg["platform_stats"]) == 4
    assert "hero_headline" in cfg
    assert "hero_subline" in cfg
    assert "hero_rubro_scenes" in cfg
    assert len(cfg["hero_rubro_scenes"]) == 4
    assert "dashboard_scene" in cfg


def test_get_config_fallback_to_es():
    cfg = get_config("mx", "fr")
    assert cfg.get("country_code") == "mx"


def test_get_config_unknown_country_returns_empty():
    cfg = get_config("xx", "es")
    assert cfg == {}


# ---------------------------------------------------------------------------
# View smoke tests — no DB (welcome views don't touch ORM)
# ---------------------------------------------------------------------------

_VIEW_CASES = [
    (bienvenida_mx,    "/mx/es/bienvenida/",  "180K+",   "refacciones",       "Vehículo"),
    (bienvenida_pe,    "/pe/es/bienvenida/",  "35K+",    "Sunat",             "Tarjeta de Propiedad"),
    (bienvenida_ar,    "/ar/es/bienvenida/",  "60K+",    "AFIP",              "08 Firmado"),
    (bienvenida_uy,    "/uy/es/bienvenida/",  "8K+",     "SUCIVE",            "Libreta de Propiedad"),
    (bienvenida_ve,    "/ve/es/bienvenida/",  "25K+",    "INTT",              "Título de Propiedad"),
    (bienvenida_co,    "/co/es/bienvenida/",  "50K+",    "DIAN",              "Tecnomecánica"),
    (bienvenida_ec,    "/ec/es/bienvenida/",  "15K+",    "SRI",               "Matrícula al día"),
    (bienvenida_br_pt, "/br/pt/bienvenida/",  "200K+",   "NF-e",              "DUT / CRLV"),
    (bienvenida_us_en, "/us/en/bienvenida/",  "160K+",   "bilingual",         "Clean Title"),
    (bienvenida_us_es, "/us/es/bienvenida/",  "160K+",   "bilingüe",          "Clean Title"),
]

_VIEW_IDS = [case[1].strip("/").replace("/", "-") for case in _VIEW_CASES]


@pytest.mark.parametrize("view_fn,path,stat,insight_word,term_value", _VIEW_CASES, ids=_VIEW_IDS)
def test_welcome_view_returns_200(view_fn, path, stat, insight_word, term_value):
    response = _get(view_fn, path)
    assert response.status_code == 200


@pytest.mark.parametrize("view_fn,path,stat,insight_word,term_value", _VIEW_CASES, ids=_VIEW_IDS)
def test_welcome_view_css_vars_injected(view_fn, path, stat, insight_word, term_value):
    html = _get(view_fn, path).content.decode()
    assert "--c1-rgb:" in html
    assert "--c2-rgb:" in html


@pytest.mark.parametrize("view_fn,path,stat,insight_word,term_value", _VIEW_CASES, ids=_VIEW_IDS)
def test_welcome_view_social_proof_stat_rendered(view_fn, path, stat, insight_word, term_value):
    html = _get(view_fn, path).content.decode()
    assert stat in html, f"social_proof stat '{stat}' not found in {path}"


@pytest.mark.parametrize("view_fn,path,stat,insight_word,term_value", _VIEW_CASES, ids=_VIEW_IDS)
def test_welcome_view_market_insight_rendered(view_fn, path, stat, insight_word, term_value):
    html = _get(view_fn, path).content.decode()
    assert insight_word.lower() in html.lower(), f"market_insight word '{insight_word}' not found in {path}"


@pytest.mark.parametrize("view_fn,path,stat,insight_word,term_value", _VIEW_CASES, ids=_VIEW_IDS)
def test_welcome_view_terminology_pills_rendered(view_fn, path, stat, insight_word, term_value):
    html = _get(view_fn, path).content.decode()
    assert term_value in html, f"terminology value '{term_value}' not found in {path}"
