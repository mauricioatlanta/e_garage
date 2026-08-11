from django.shortcuts import render
from django.utils import translation

from taller.welcome_config import get_config
from taller.models.public_page_view import PublicPageView
from taller.services.public_analytics import track_public_page


def bienvenida_view(request, country: str, lang: str = "es"):
    track_public_page(
        request,
        page_type=PublicPageView.PAGE_WELCOME,
        country=country,
        language=lang,
    )

    config = get_config(country, lang)
    translation.activate(lang)
    context = {**config, "lang": lang}
    template = f"{country}/{lang}/onboarding/bienvenida.html"
    response = render(request, template, context)
    response.set_cookie("django_language", lang)
    return response


# ── Country wrappers ──────────────────────────────────────────────────────────

def bienvenida_mx(request):    return bienvenida_view(request, "mx", "es")
def bienvenida_pe(request):    return bienvenida_view(request, "pe", "es")
def bienvenida_ar(request):    return bienvenida_view(request, "ar", "es")
def bienvenida_uy(request):    return bienvenida_view(request, "uy", "es")
def bienvenida_ve(request):    return bienvenida_view(request, "ve", "es")
def bienvenida_co(request):    return bienvenida_view(request, "co", "es")
def bienvenida_ec(request):    return bienvenida_view(request, "ec", "es")
def bienvenida_br_es(request): return bienvenida_view(request, "br", "es")
def bienvenida_br_pt(request): return bienvenida_view(request, "br", "pt")
def bienvenida_us_en(request): return bienvenida_view(request, "us", "en")
def bienvenida_us_es(request): return bienvenida_view(request, "us", "es")


# ── Aliases for backward-compat with gestion_taller/urls.py ──────────────────
bienvenida_usa_en = bienvenida_us_en
bienvenida_usa_es = bienvenida_us_es


def _render_bienvenida_usa(request, forced_lang=None):
    """Legacy helper kept for any code that still calls it directly."""
    session_lang = request.session.get("django_language")
    cookie_lang = request.COOKIES.get("django_language")
    if forced_lang in ("en", "es"):
        lang = forced_lang
    elif session_lang in ("en", "es"):
        lang = session_lang
    elif cookie_lang in ("en", "es"):
        lang = cookie_lang
    else:
        lang = "en"
    return bienvenida_view(request, "us", lang)
