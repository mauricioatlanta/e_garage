"""
URLs específicas para Brasil 🇧🇷
Patrón base: /br/
Brasil: SOLO portugués (pt).
Compatibilidad: /br/es/... redirige a /br/pt/...
"""

from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import RedirectView

from taller.views.country_aware_auth import country_aware_login
from taller.views_extra.bienvenida import bienvenida_br_es, bienvenida_br_pt
from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_brasil"


urlpatterns = [
    # /br/ → /br/pt/bienvenida/
    path("", RedirectView.as_view(url="/br/pt/bienvenida/", permanent=False)),
    # /br/pt/ → /br/pt/bienvenida/ (entrypoint del funnel BR)
    path("pt/", RedirectView.as_view(url="/br/pt/bienvenida/", permanent=False)),
    # --- PORTUGUÉS (principal) ---
    path("pt/bienvenida/", bienvenida_br_pt, name="bienvenida_pt"),
    path(
        "pt/accounts/signup/",
        lambda r: signup_redirect(r, "br"),
        name="signup_pt",
    ),
    path(
        "pt/accounts/login/",
        country_aware_login,
        name="account_login",
    ),
    # Redirect /br/pt/accounts/* → /accounts/* (allauth montado solo en gestion_taller/urls)
    path(
        "pt/accounts/",
        lambda r: redirect("/accounts/" + ("?" + r.GET.urlencode() if r.GET else "")),
    ),
    path(
        "pt/accounts/<path:rest>",
        lambda r, rest: redirect(
            "/accounts/" + rest.rstrip("/") + ("?" + r.GET.urlencode() if r.GET else "")
        ),
    ),
    path(
        "login/",
        lambda r: redirect("/br/pt/accounts/login/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="account_login_short",
    ),
    # --- ESPAÑOL ---
    path("es/", RedirectView.as_view(url="/br/es/bienvenida/", permanent=False)),
    path("es/bienvenida/", bienvenida_br_es, name="bienvenida_es"),
    path(
        "es/reportes/",
        include(("taller.reportes.urls", "reportes_br_es"), namespace="reportes_br_es"),
    ),
    path(
        "pt/reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes"),
    ),
    # Brasil es SOLO pt: cualquier /br/es/<resto> -> /br/pt/<resto>
    path(
        "es/<path:rest>",
        lambda r, rest: redirect(f"/br/pt/{rest}" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="br_es_catchall",
    ),
    # Clientes Brasil - faltaba, por eso /clientes/ daba Vista no encontrada
    # pt es principal, es redirige a pt (igual que reportes)
    path(
        "pt/clientes/",
        include(("taller.clientes.urls", "clientes"), namespace="clientes"),
    ),
    path(
        "es/clientes/",
        RedirectView.as_view(url="/br/pt/clientes/", query_string=True, permanent=False),
        name="clientes_es_redirect",
    ),
    path(
        "es/clientes/<path:rest>",
        lambda r, rest: redirect(f"/br/pt/clientes/{rest}" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="clientes_es_rest_redirect",
    ),
]
