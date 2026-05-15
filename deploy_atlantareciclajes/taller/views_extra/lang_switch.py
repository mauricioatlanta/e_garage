from django.contrib import messages
from django.shortcuts import redirect
from django.utils import translation
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

ALLOWED_BY_COUNTRY = {"US": ("en", "es")}


@require_POST
@csrf_protect
def set_language_us(request):
    # Verificar si es USA desde empresa o desde URL
    empresa = getattr(request, "empresa", None)
    pais = None

    if empresa:
        pais = empresa.pais
    elif request.path.startswith("/us/"):
        pais = "US"

    if not pais or pais != "US":
        messages.error(request, "Cambio de idioma no permitido para tu país.")
        return redirect(request.POST.get("next") or "/")

    lang = request.POST.get("language")
    if lang in ALLOWED_BY_COUNTRY["US"]:
        # Usar la clave estándar de Django para el idioma
        request.session["django_language"] = lang
        # También guardar en preferred_lang para compatibilidad
        request.session["preferred_lang"] = lang
        # Marcar la sesión como modificada para forzar el guardado
        request.session.modified = True
        # Activar el idioma inmediatamente
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        messages.success(request, "Language updated." if lang == "en" else "Idioma actualizado.")
    else:
        messages.error(
            request,
            "Language not allowed." if request.LANGUAGE_CODE == "en" else "Idioma no permitido.",
        )

    next_url = request.POST.get("next") or "/"
    # Asegurar que la redirección preserve el idioma
    response = redirect(next_url)
    # Establecer el idioma en la cookie también para que LocaleMiddleware lo respete
    from django.conf import settings

    # Usar valores por defecto si no están configurados
    cookie_name = getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language")
    cookie_age = getattr(settings, "LANGUAGE_COOKIE_AGE", 60 * 60 * 24 * 365)  # 1 año por defecto
    cookie_path = getattr(settings, "LANGUAGE_COOKIE_PATH", "/")
    cookie_domain = getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None)
    cookie_secure = getattr(settings, "LANGUAGE_COOKIE_SECURE", False)
    cookie_httponly = getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False)
    cookie_samesite = getattr(settings, "LANGUAGE_COOKIE_SAMESITE", "Lax")

    response.set_cookie(
        cookie_name,
        lang,
        max_age=cookie_age,
        path=cookie_path,
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=cookie_httponly,
        samesite=cookie_samesite,
    )
    return response
