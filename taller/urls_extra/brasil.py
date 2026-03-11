"""
URLs específicas para Brasil 🇧🇷
Patrón base: /br/
Brasil: SOLO portugués (pt).
Compatibilidad: /br/es/... redirige a /br/pt/...
"""

from django.shortcuts import redirect
from django.urls import path
from django.utils import translation
from django.views.generic import RedirectView, TemplateView

from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_brasil"


class BrasilPTTemplateView(TemplateView):
    template_name = "br/pt/onboarding/bienvenida.html"

    def dispatch(self, request, *args, **kwargs):
        translation.activate("pt-br")
        request.LANGUAGE_CODE = "pt-br"
        return super().dispatch(request, *args, **kwargs)


urlpatterns = [
    # /br/ → /br/pt/bienvenida/
    path("", RedirectView.as_view(url="/br/pt/bienvenida/", permanent=False)),
    # --- PORTUGUÉS (principal) ---
    path(
        "pt/bienvenida/",
        BrasilPTTemplateView.as_view(),
        name="bienvenida_pt",
    ),
    path(
        "pt/accounts/signup/",
        lambda r: signup_redirect(r, "br"),
        name="signup_pt",
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
    # --- ESPAÑOL (legacy) → redirige a PT ---
    path("es/", RedirectView.as_view(url="/br/pt/bienvenida/", permanent=False)),
    path("es/bienvenida/", RedirectView.as_view(url="/br/pt/bienvenida/", permanent=False)),
]
