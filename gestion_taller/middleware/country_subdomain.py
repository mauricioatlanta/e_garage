from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_COUNTRIES = {"cl", "us", "br", "pe", "mx", "co", "ec", "ve", "uy", "ar"}


@dataclass(frozen=True)
class HostCountryInfo:
    country: str | None
    uses_subdomain: bool


def resolve_country_from_host(host: str) -> HostCountryInfo:
    normalized_host = (host or "").split(":")[0].lower()

    root_hosts = {
        "egarage.cl",
        "www.egarage.cl",
        "localhost",
        "127.0.0.1",
    }

    if normalized_host in root_hosts:
        return HostCountryInfo(country=None, uses_subdomain=False)

    parts = normalized_host.split(".")
    if len(parts) >= 3:
        subdomain = parts[0]
        apex = ".".join(parts[-2:])
        if apex == "egarage.cl" and subdomain in SUPPORTED_COUNTRIES:
            return HostCountryInfo(country=subdomain, uses_subdomain=True)

    return HostCountryInfo(country=None, uses_subdomain=False)


class CountrySubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        info = resolve_country_from_host(request.get_host())
        request.country_from_host = info.country
        request.uses_country_subdomain = info.uses_subdomain

        # Exponer tambien `request.country` temprano permite que middleware y
        # vistas legacy reutilicen el pais inferido desde el host.
        if info.country:
            request.country = info.country.upper()
            request.country_code = info.country.upper()

        return self.get_response(request)
