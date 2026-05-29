import re
from urllib.parse import urlparse, urlunparse

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import translation
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

ALLOWED_BY_COUNTRY = {"US": ("en", "es")}


@require_POST
@csrf_protect
def set_language_us(request):
    # Verificar si es USA desde empresa, desde URL o desde parámetro next
    empresa = getattr(request, "empresa", None)
    pais = None

    if empresa:
        pais = empresa.pais
    elif request.path.startswith("/us/"):
        pais = "US"
    else:
        # Si no detectamos desde path, verificar en el parámetro next
        next_url = request.POST.get("next", "")
        if next_url.startswith("/us/") or "/us/" in next_url:
            pais = "US"

    if not pais or pais != "US":
        messages.error(request, "Cambio de idioma no permitido para tu país.")
        return redirect(request.POST.get("next") or "/")

    lang = request.POST.get("language")
    if not lang or lang not in ALLOWED_BY_COUNTRY["US"]:
        messages.error(
            request,
            (
                "Language not allowed."
                if getattr(request, "LANGUAGE_CODE", "en") == "en"
                else "Idioma no permitido."
            ),
        )
        return redirect(request.POST.get("next") or "/")

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

    next_url = request.POST.get("next") or "/"

    # Separar la URL de los parámetros de consulta si existen
    parsed = urlparse(next_url)
    path = parsed.path

    # Actualizar la URL para reflejar el cambio de idioma
    # Usar expresión regular para reemplazar el código de idioma en URLs como /us/es/... o /us/en/...

    # Patrón para detectar /us/es/ o /us/en/ y reemplazarlo
    pattern = r"^/us/(es|en)/"
    if re.match(pattern, path):
        # Reemplazar el código de idioma existente con el nuevo
        path = re.sub(pattern, f"/us/{lang}/", path)
    # Si la URL tiene /us/ pero no está en el formato /us/xx/
    elif "/us/" in path:
        # Si la URL es /us/... sin código de idioma, agregarlo
        if not re.match(r"^/us/(es|en)/", path):
            path = re.sub(r"^/us/", f"/us/{lang}/", path)
    # Para URLs que no son de US, también intentar reemplazar /es/ o /en/ si existen
    elif lang == "en" and "/es/" in path:
        path = path.replace("/es/", "/en/", 1)  # Solo reemplazar la primera ocurrencia
    elif lang == "es" and "/en/" in path:
        path = path.replace("/en/", "/es/", 1)  # Solo reemplazar la primera ocurrencia

    # Reconstruir la URL con los parámetros de consulta preservados
    next_url = urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )

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
