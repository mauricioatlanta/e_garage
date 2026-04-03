from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.conf import settings
from django.utils.translation import get_language


COUNTRY_LANGUAGE_POLICY = {
    "US": {"default": "en", "allowed": ("en", "es")},
    "BR": {"default": "pt", "allowed": ("pt",)},
    "CL": {"default": "es", "allowed": ("es",)},
    "MX": {"default": "es", "allowed": ("es",)},
    "CO": {"default": "es", "allowed": ("es",)},
    "EC": {"default": "es", "allowed": ("es",)},
    "PE": {"default": "es", "allowed": ("es",)},
    "VE": {"default": "es", "allowed": ("es",)},
    "UY": {"default": "es", "allowed": ("es",)},
    "AR": {"default": "es", "allowed": ("es",)},
}

COUNTRY_ALIASES = {
    "USA": "US",
    "CHILE": "CL",
    "MEXICO": "MX",
    "PERU": "PE",
    "PERÚ": "PE",
    "COLOMBIA": "CO",
    "ECUADOR": "EC",
    "VENEZUELA": "VE",
    "BRASIL": "BR",
    "BRAZIL": "BR",
    "URUGUAY": "UY",
    "ARGENTINA": "AR",
}

CANONICAL_ENTRY_ALIASES = {
    "login": "accounts/login/",
    "signup": "accounts/signup/",
    "workspace": "workspace/",
    "workspace/buscar": "workspace/buscar/",
}


@dataclass(frozen=True)
class PathMatch:
    country: str | None
    lang: str | None
    rest: str


def normalize_country(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).strip().upper()
    normalized = COUNTRY_ALIASES.get(normalized, normalized)
    return normalized if normalized in COUNTRY_LANGUAGE_POLICY else None


def default_country() -> str:
    return normalize_country(getattr(settings, "EGARAGE_DEFAULT_COUNTRY", "CL")) or "CL"


def allowed_langs_for_country(country: str | None) -> tuple[str, ...]:
    normalized = normalize_country(country) or default_country()
    return tuple(COUNTRY_LANGUAGE_POLICY.get(normalized, COUNTRY_LANGUAGE_POLICY["CL"])["allowed"])


def default_lang_for_country(country: str | None) -> str:
    normalized = normalize_country(country) or default_country()
    return str(COUNTRY_LANGUAGE_POLICY.get(normalized, COUNTRY_LANGUAGE_POLICY["CL"])["default"])


def canonical_lang_for_country(country: str | None, requested_lang: str | None = None) -> str:
    allowed = allowed_langs_for_country(country)
    lang = (requested_lang or "").strip().lower()
    return lang if lang in allowed else default_lang_for_country(country)


def canonical_prefix(country: str | None, lang: str | None = None) -> str:
    normalized = normalize_country(country) or default_country()
    resolved_lang = canonical_lang_for_country(normalized, lang)
    return f"/{normalized.lower()}/{resolved_lang}"


def parse_country_lang(path: str | None) -> PathMatch:
    raw_path = (path or "/").strip() or "/"
    parts = [part for part in raw_path.strip("/").split("/") if part]
    if not parts:
        return PathMatch(country=None, lang=None, rest="/")

    country = normalize_country(parts[0])
    if not country:
        return PathMatch(
            country=None, lang=None, rest=raw_path if raw_path.startswith("/") else f"/{raw_path}"
        )

    lang = None
    rest_start = 1
    if len(parts) > 1 and parts[1].lower() in {"en", "es", "pt"}:
        lang = parts[1].lower()
        rest_start = 2

    rest_parts = parts[rest_start:]
    rest = "/" + "/".join(rest_parts) if rest_parts else "/"
    return PathMatch(country=country, lang=lang, rest=rest)


def canonicalize_entry_alias(rest: str) -> str:
    normalized = (rest or "/").strip("/").lower()
    target = CANONICAL_ENTRY_ALIASES.get(normalized)
    return f"/{target}" if target else rest or "/"


def infer_country_from_user(user) -> str | None:
    if not getattr(user, "is_authenticated", False):
        return None

    empresa = getattr(user, "empresa", None)
    country = normalize_country(getattr(empresa, "pais", None)) if empresa else None
    if country:
        return country

    perfil = getattr(user, "perfil", None)
    return normalize_country(getattr(perfil, "pais", None)) if perfil else None


def infer_country_from_next(next_url: str | None) -> str | None:
    if not next_url or not str(next_url).startswith("/"):
        return None
    return parse_country_lang(next_url).country


def infer_country(
    request,
    *,
    fallback: str | None = None,
    session_keys: Iterable[str] = ("country", "preferred_country", "pending_signup_country"),
) -> str:
    country = infer_country_from_user(getattr(request, "user", None))
    if country:
        return country

    path_match = parse_country_lang(getattr(request, "path", "/"))
    if path_match.country:
        return path_match.country

    next_country = infer_country_from_next(
        request.GET.get("next") or request.POST.get("next") or request.GET.get("redirect_to")
    )
    if next_country:
        return next_country

    from_param = normalize_country(request.GET.get("from") or request.POST.get("from"))
    if from_param:
        return from_param

    for key in session_keys:
        session_country = normalize_country(request.session.get(key))
        if session_country:
            return session_country

    request_country = normalize_country(getattr(request, "country", None))
    if request_country:
        return request_country

    return normalize_country(fallback) or default_country()


def infer_language(request, country: str | None, path_lang: str | None = None) -> str:
    if path_lang:
        return canonical_lang_for_country(country, path_lang)

    session_lang = request.session.get("django_language")
    if session_lang in allowed_langs_for_country(country):
        return session_lang

    cookie_lang = request.COOKIES.get("django_language")
    if cookie_lang in allowed_langs_for_country(country):
        return cookie_lang

    active_lang = get_language()
    if active_lang in allowed_langs_for_country(country):
        return active_lang

    return default_lang_for_country(country)
