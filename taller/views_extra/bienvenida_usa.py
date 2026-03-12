from django.shortcuts import render
from django.utils import translation


def _render_bienvenida_usa(request, forced_lang=None):
    """
    Renderiza la bienvenida de USA respetando idioma forzado,
    sesión/cookie o fallback a inglés.
    """
    session_lang = request.session.get("django_language")
    cookie_lang = request.COOKIES.get("django_language")

    if forced_lang in ["en", "es"]:
        lang = forced_lang
    elif session_lang in ["en", "es"]:
        lang = session_lang
    elif cookie_lang in ["en", "es"]:
        lang = cookie_lang
    else:
        lang = "en"

    translation.activate(lang)

    context = {
        "LANGUAGE_CODE": lang,
        "page_title": "eGarage USA - Professional Automotive Management",
        "is_usa_market": True,
    }

    if lang == "es":
        template_name = "us/es/onboarding/bienvenida.html"
    else:
        template_name = "us/en/onboarding/bienvenida.html"

    response = render(request, template_name, context)
    response.set_cookie("django_language", lang)
    return response


def bienvenida_usa(request):
    return _render_bienvenida_usa(request)


def bienvenida_usa_es(request):
    return _render_bienvenida_usa(request, forced_lang="es")


def bienvenida_usa_en(request):
    return _render_bienvenida_usa(request, forced_lang="en")
