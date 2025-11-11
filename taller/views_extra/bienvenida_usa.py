from django.shortcuts import render
from django.utils import translation


def bienvenida_usa(request):
    # NO forzar idioma - dejar que el middleware y Django i18n lo manejen
    # El usuario puede cambiar idioma con el selector

    # Debug: ver TODO lo que hay en la sesión
    print(f"[DEBUG] bienvenida_usa - TODAS las claves de sesión: {list(request.session.keys())}")
    print(f"[DEBUG] bienvenida_usa - Sesión completa: {dict(request.session)}")

    # Detectar idioma preferido del usuario
    session_lang = request.session.get("django_language")
    print(f"[DEBUG] bienvenida_usa - django_language en sesión: {session_lang}")

    # También revisar cookies
    cookie_lang = request.COOKIES.get("django_language")
    print(f"[DEBUG] bienvenida_usa - django_language en cookie: {cookie_lang}")

    if session_lang in ["en", "es"]:
        translation.activate(session_lang)
        print(f"[DEBUG] bienvenida_usa - Usando idioma de sesión: {session_lang}")
    elif cookie_lang in ["en", "es"]:
        translation.activate(cookie_lang)
        print(f"[DEBUG] bienvenida_usa - Usando idioma de cookie: {cookie_lang}")
    else:
        # Default para USA es inglés
        translation.activate("en")
        print("[DEBUG] bienvenida_usa - Sin preferencia, usando default: en")

    # Create context with language code
    context = {
        "LANGUAGE_CODE": translation.get_language(),
        "page_title": "eGarage USA - Professional Automotive Management",
        "is_usa_market": True,
    }

    print(f"[DEBUG] bienvenida_usa - Idioma final: {translation.get_language()}")

    return render(request, "onboarding/bienvenida_usa.html", context)
