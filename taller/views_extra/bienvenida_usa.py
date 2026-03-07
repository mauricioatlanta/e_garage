import logging
import traceback

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import translation

logger = logging.getLogger(__name__)


def bienvenida_usa(request):
    # NO forzar idioma - dejar que el middleware y Django i18n lo manejen
    # El usuario puede cambiar idioma con el selector

    # Detectar idioma preferido del usuario
    session_lang = request.session.get("django_language")
    cookie_lang = request.COOKIES.get("django_language")

    if session_lang in ["en", "es"]:
        translation.activate(session_lang)
    elif cookie_lang in ["en", "es"]:
        translation.activate(cookie_lang)
    else:
        translation.activate("en")

    # Create context with language code
    context = {
        "LANGUAGE_CODE": translation.get_language(),
        "page_title": "eGarage USA - Professional Automotive Management",
        "is_usa_market": True,
    }

    # Usar template según el idioma detectado
    lang = translation.get_language()
    if lang == "es":
        template_name = "us/es/onboarding/bienvenida.html"
    else:
        # Fallback a inglés o template genérico
        template_name = "us/en/onboarding/bienvenida.html"

    return render(request, template_name, context)


def bienvenida_usa_en(request, *args, **kwargs):
    """Vista de bienvenida USA en inglés: fuerza idioma 'en' para /us/en/bienvenida/."""
    try:
        translation.activate("en")
        request.LANGUAGE_CODE = "en"
        context = {
            "LANGUAGE_CODE": "en",
            "page_title": "eGarage USA - Professional Automotive Management",
            "is_usa_market": True,
        }
        return render(request, "us/en/onboarding/bienvenida.html", context)
    except Exception as e:
        logger.exception("bienvenida_usa_en failed")
        return HttpResponse(
            f"Error loading bienvenida (en): {e!s}. Check gunicorn/journalctl logs.",
            status=500,
            content_type="text/plain",
        )


def bienvenida_usa_es(request, *args, **kwargs):
    """Vista de bienvenida USA en español: fuerza idioma 'es' para /us/es/bienvenida/."""
    try:
        translation.activate("es")
        request.LANGUAGE_CODE = "es"
        context = {
            "LANGUAGE_CODE": "es",
            "page_title": "eGarage USA - Gestión Profesional de Talleres",
            "is_usa_market": True,
        }
        return render(request, "us/es/onboarding/bienvenida.html", context)
    except Exception as e:
        logger.exception("bienvenida_usa_es failed")
        return HttpResponse(
            f"Error loading bienvenida (es): {e!s}. Check gunicorn/journalctl logs.",
            status=500,
            content_type="text/plain",
        )
