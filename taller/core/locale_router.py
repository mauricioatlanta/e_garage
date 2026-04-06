from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_ROUTES = {
    "CL": {"default_lang": "es", "langs": {"es"}, "url": "/cl/es/"},
    "US": {
        "default_lang": "en",
        "langs": {"en", "es"},
        "url_map": {"en": "/us/en/", "es": "/us/es/"},
    },
}

DEFAULT_COUNTRY = "CL"
DEFAULT_LANG = "es"


@dataclass(frozen=True)
class RouteDecision:
    country: str
    lang: str
    target_url: str
    source: str


def normalize_country(raw: str | None) -> str:
    if not raw:
        return DEFAULT_COUNTRY
    value = raw.strip().upper()
    return value if value in SUPPORTED_ROUTES else DEFAULT_COUNTRY


def normalize_lang(country: str, raw: str | None) -> str:
    cfg = SUPPORTED_ROUTES[country]
    allowed = cfg["langs"]

    if not raw:
        return cfg["default_lang"]

    value = raw.strip().lower()
    if value in allowed:
        return value

    return cfg["default_lang"]


def parse_accept_language(header: str | None) -> str | None:
    if not header:
        return None

    parts = [part.strip().lower() for part in header.split(",") if part.strip()]
    for part in parts:
        code = part.split(";")[0]
        base = code.split("-")[0]
        if base in {"es", "en", "pt"}:
            return base
    return None


def build_target_url(country: str, lang: str) -> str:
    cfg = SUPPORTED_ROUTES[country]
    if "url_map" in cfg:
        return cfg["url_map"][lang]
    return cfg["url"]


def resolve_country_lang(
    *,
    cookie_country: str | None,
    cookie_lang: str | None,
    cf_country: str | None,
    accept_language: str | None,
) -> RouteDecision:
    if cookie_country:
        country = normalize_country(cookie_country)
        lang = normalize_lang(country, cookie_lang)
        return RouteDecision(
            country=country,
            lang=lang,
            target_url=build_target_url(country, lang),
            source="cookie",
        )

    country = normalize_country(cf_country)
    browser_lang = parse_accept_language(accept_language)
    lang = normalize_lang(country, browser_lang)

    return RouteDecision(
        country=country,
        lang=lang,
        target_url=build_target_url(country, lang),
        source="auto",
    )
