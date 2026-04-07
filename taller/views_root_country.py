from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse

from .utils.empresa import get_active_empresa


PUBLIC_ROUTE_BY_NAMESPACE = {
    "us_en": "us_en_bienvenida",
    "us_es": "us_es_bienvenida",
    "chile": "chile:bienvenida_chile_alt",
    "uruguay_es": "uruguay_es:bienvenida_uruguay_alt",
    "peru": "peru:bienvenida_peru",
    "colombia": "colombia:bienvenida_colombia",
    "ecuador": "ecuador:bienvenida_ecuador",
    "venezuela": "venezuela:bienvenida_venezuela",
    "mexico": "mexico:bienvenida_mexico",
    "brasil": "brasil:bienvenida_pt",
    "argentina": "argentina:bienvenida_argentina_alt",
}


def _reverse_country_route(namespace: str | None, leaf: str) -> str:
    candidates: list[str] = []
    country_prefix = namespace.split("_", 1)[0] if namespace else None
    if namespace:
        candidates.extend(
            [
                f"{namespace}:{leaf}",
                f"{namespace}:taller:{leaf}",
            ]
        )
        if country_prefix:
            candidates.append(f"{namespace}:{country_prefix}_taller:{leaf}")
    candidates.append(f"taller:{leaf}")

    for name in candidates:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise NoReverseMatch(f"No route found for {leaf!r} in namespace {namespace!r}")


def country_lang_root_view(request: HttpRequest) -> HttpResponse:
    namespace = request.resolver_match.namespace if request.resolver_match else None

    if not request.user.is_authenticated:
        public_target = PUBLIC_ROUTE_BY_NAMESPACE.get(namespace)
        return redirect(public_target) if public_target else redirect("home")

    empresa = get_active_empresa(request)
    if not empresa:
        return redirect(_reverse_country_route(namespace, "onboarding"))

    if not getattr(empresa, "onboarding_completado", False):
        return redirect(_reverse_country_route(namespace, "onboarding"))

    return redirect(_reverse_country_route(namespace, "centro_trabajo"))
