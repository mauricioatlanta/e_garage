"""
International Content Engine.

get_landing_context(country_key, vertical_key) → dict ready for Django's render().

country_key : one of cl · ar · pe · mx · ec · ve · br · us_en · us_es
vertical_key: one of workshop · parts · salvage · tire · carwash
"""

from taller.country.content import COUNTRY_CONTENT
from taller.country.hub import COUNTRY_HUB
from taller.country.verticals import VERTICAL_CONTENT
from taller.country.verticals import URL_SLUG_TO_VERTICAL as _BASE_SLUG_MAP

# Comprehensive slug → vertical map: generic slugs + every country-specific slug.
# Generic slugs (from verticals.py) stay valid as permanent aliases.
URL_SLUG_TO_VERTICAL: dict[str, str] = dict(_BASE_SLUG_MAP)
for _cdata in COUNTRY_CONTENT.values():
    for _vk, _slug in _cdata.get("vertical_slugs", {}).items():
        URL_SLUG_TO_VERTICAL[_slug] = _vk

# Country key → URL prefix used in paths
_COUNTRY_CODE_MAP = {
    "cl": "cl", "ar": "ar", "pe": "pe", "mx": "mx",
    "ec": "ec", "ve": "ve", "br": "br",
    "us_en": "us/en", "us_es": "us/es",
}


def _fmt(s: str, subs: dict) -> str:
    """String-format with substitutions; leave unreplaced placeholders intact."""
    try:
        return s.format_map(subs)
    except (KeyError, ValueError):
        return s


def _fmt_list(items: list, subs: dict) -> list:
    result = []
    for item in items:
        result.append({
            k: _fmt(v, subs) if isinstance(v, str) else v
            for k, v in item.items()
        })
    return result


_NAV = {
    "en": ("Sign in",    "Create account"),
    "pt": ("Entrar",     "Criar conta"),
    "es": ("Ingresar",   "Registrarse"),
}
_FOOTER_HOME = {"en": "Home", "pt": "Início", "es": "Inicio"}
_FOOTER_COLORS = ["hover:text-cyan-400", "hover:text-fuchsia-400",
                  "hover:text-lime-400", "hover:text-sky-400", "hover:text-amber-400"]
_FOOTER_VERTICALS = ["workshop", "salvage", "parts", "carwash", "tire"]


def get_landing_context(country_key: str, vertical_key: str) -> dict:
    country = COUNTRY_CONTENT[country_key]
    vertical = VERTICAL_CONTENT[vertical_key]
    hub = COUNTRY_HUB[country_key]
    language = country["language"]

    text = vertical.get(language) or vertical.get("es")

    # Substitution variables: merge country + hub flat fields
    subs = {k: v for k, v in country.items() if isinstance(v, (str, int, float))}
    subs.update({k: v for k, v in hub.items() if isinstance(v, (str, int, float))})

    def fmt(s: str) -> str:
        return _fmt(s, subs)

    def fmt_list(items: list) -> list:
        return _fmt_list(items, subs)

    case = country.get("cases", {}).get(vertical_key)
    testimonial = country.get("testimonials", {}).get(vertical_key)

    if case:
        case = {
            **case,
            "before_label": fmt(case.get("before_label", "")),
            "before_text": fmt(case.get("before_text", "")),
            "after_label": fmt(case.get("after_label", "")),
            "after_text": fmt(case.get("after_text", "")),
            "metrics": _fmt_list(case.get("metrics", []), subs),
        }

    url_prefix = _COUNTRY_CODE_MAP.get(country_key, country_key)
    # Prefer country-specific slug; fall back to language slug from vertical definition
    country_slug = country.get("vertical_slugs", {}).get(vertical_key)
    if not country_slug:
        country_slug = vertical["url_slug"].get(language, vertical["url_slug"].get("es", vertical_key))
    vertical_slug = country_slug

    return {
        # ── SEO ──────────────────────────────────────────────────────────
        "seo_title": fmt(text.get("seo_title", "")),
        "meta_description": fmt(text.get("meta_description", "")),
        "canonical_path": f"/{url_prefix}/{vertical_slug}/",
        "og_title": fmt(text.get("og_title", "")),
        "og_description": fmt(text.get("meta_description", "")),

        # ── Vertical identity ─────────────────────────────────────────────
        "vertical_key": vertical_key,
        "vertical_slug": vertical_slug,
        "rubro_key": vertical["rubro_key"],
        "scene_image": vertical["scene_image"],
        "tw": vertical["tw"],

        # ── Hero ─────────────────────────────────────────────────────────
        "hero_badge": fmt(text.get("hero_badge", "")),
        "hero_setup": fmt(text.get("hero_setup", "")),
        "hero_h1": fmt(text.get("hero_h1", "")),
        "hero_subheadline": fmt(text.get("hero_subheadline", "")),
        "hero_cta_primary": text.get("hero_cta_primary", ""),
        "hero_cta_secondary": text.get("hero_cta_secondary", ""),
        "hero_caption": fmt(text.get("hero_caption", "")),

        # ── Problems ──────────────────────────────────────────────────────
        "problems_heading": fmt(text.get("problems_heading", "")),
        "problems": fmt_list(text.get("problems", [])),

        # ── Case study ────────────────────────────────────────────────────
        "case_heading": fmt(text.get("case_heading", "")),
        "case_study": case,

        # ── Benefits ──────────────────────────────────────────────────────
        "benefits_heading": fmt(text.get("benefits_heading", "")),
        "benefits": fmt_list(text.get("benefits", [])),

        # ── Steps ────────────────────────────────────────────────────────
        "steps_heading": fmt(text.get("steps_heading", "")),
        "steps": fmt_list(text.get("steps", [])),

        # ── Testimonial ───────────────────────────────────────────────────
        "testimonial": testimonial,

        # ── CTAs ──────────────────────────────────────────────────────────
        "cta_mid_heading": fmt(text.get("cta_mid_heading", "")),
        "cta_mid_subtext": fmt(text.get("cta_mid_subtext", "")),
        "cta_button_primary": text.get("cta_button_primary", ""),

        "cta_final_heading": fmt(text.get("cta_final_heading", "")),
        "cta_final_subtext": fmt(text.get("cta_final_subtext", "")),
        "cta_final_button": text.get("cta_final_button", ""),
        "cta_final_note": fmt(text.get("cta_final_note", "")),

        # ── FAQ ──────────────────────────────────────────────────────────
        "faq_heading": fmt(text.get("faq_heading", "")),
        "faqs": fmt_list(text.get("faqs", [])),
        "faq_country_q": country.get("faq_country_q", ""),
        "faq_country_a": country.get("faq_country_a", ""),

        # ── Country primitives (for template fallback) ────────────────────
        **{k: v for k, v in country.items() if isinstance(v, (str, int, float))},
        **{k: v for k, v in hub.items() if isinstance(v, (str, int, float))},

        # ── Language ─────────────────────────────────────────────────────
        "language": language,

        # ── Nav labels ───────────────────────────────────────────────────
        "nav_login":   _NAV.get(language, _NAV["es"])[0],
        "nav_signup":  _NAV.get(language, _NAV["es"])[1],
        "footer_home": _FOOTER_HOME.get(language, "Inicio"),

        # ── Footer links: one per vertical with name + country URL + color ─
        "landing_urls": get_hub_landing_urls(country_key),
        "footer_links": [
            {
                "name":  hub.get(f"{vk}_name", vk),
                "url":   f"/{url_prefix}/{country.get('vertical_slugs', {}).get(vk, vk)}/",
                "color": _FOOTER_COLORS[i],
            }
            for i, vk in enumerate(_FOOTER_VERTICALS)
        ],
    }


def get_hub_landing_urls(country_key: str) -> dict:
    """Return {vertical_key: url_path} for hub_country.html card links."""
    country = COUNTRY_CONTENT.get(country_key, {})
    url_prefix = _COUNTRY_CODE_MAP.get(country_key, country_key)
    slugs = country.get("vertical_slugs", {})
    return {vk: f"/{url_prefix}/{slug}/" for vk, slug in slugs.items()}
