from __future__ import annotations

from taller.utils.country_routing import canonical_lang_for_country, normalize_country


def build_country_lang_path(
    request,
    country_code: str,
    lang_code: str | None,
    suffix: str = "/",
) -> str:
    normalized_country = (normalize_country(country_code) or "CL").lower()
    normalized_lang = canonical_lang_for_country(normalized_country, lang_code)

    normalized_suffix = suffix or "/"
    if not normalized_suffix.startswith("/"):
        normalized_suffix = f"/{normalized_suffix}"

    if getattr(request, "uses_country_subdomain", False):
        return f"/{normalized_lang}{normalized_suffix}"

    return f"/{normalized_country}/{normalized_lang}{normalized_suffix}"
