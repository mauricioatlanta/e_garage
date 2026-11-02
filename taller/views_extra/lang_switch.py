
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
    empresa = getattr(request, "empresa", None)
    pais = None
    next_url = request.POST.get("next", "")

    if next_url.startswith("/us/") or "/us/" in next_url:
        pais = "US"
    elif empresa:
        pais = empresa.pais
    elif request.path.startswith("/us/"):
        pais = "US"

    if not pais or pais != "US":
        messages.error(request, "Cambio de idioma no permitido para tu país.")
        return redirect(request.POST.get("next") or "/")

    lang = request.POST.get("language")
    if not lang or lang not in ALLOWED_BY_COUNTRY["US"]:
        messages.error(request, "Language not allowed." if getattr(request, "LANGUAGE_CODE", "en") == "en" else "Idioma no permitido.")
        return redirect(request.POST.get("next") or "/")

    request.session["django_language"] = lang
    request.session["preferred_lang"] = lang
    request.session.modified = True
    translation.activate(lang)
    request.LANGUAGE_CODE = lang
    messages.success(request, "Language updated." if lang == "en" else "Idioma actualizado.")

    next_url = request.POST.get("next") or "/"
    parsed = urlparse(next_url)
    path = parsed.path
    pattern = r"^/us/(es|en)/"
    if re.match(pattern, path):
        path = re.sub(pattern, f"/us/{lang}/", path)
    elif "/us/" in path:
        if not re.match(r"^/us/(es|en)/", path):
            path = re.sub(r"^/us/", f"/us/{lang}/", path)
    elif lang == "en" and "/es/" in path:
        path = path.replace("/es/", "/en/", 1)
    elif lang == "es" and "/en/" in path:
        path = path.replace("/en/", "/es/", 1)

    next_url = urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))
    response = redirect(next_url)
    from django.conf import settings
    cookie_name = getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language")
    cookie_age = getattr(settings, "LANGUAGE_COOKIE_AGE", 60*60*24*365)
    cookie_path = getattr(settings, "LANGUAGE_COOKIE_PATH", "/")
    cookie_domain = getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None)
    cookie_secure = getattr(settings, "LANGUAGE_COOKIE_SECURE", False)
    cookie_httponly = getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False)
    cookie_samesite = getattr(settings, "LANGUAGE_COOKIE_SAMESITE", "Lax")
    response.set_cookie(cookie_name, lang, max_age=cookie_age, path=cookie_path, domain=cookie_domain, secure=cookie_secure, httponly=cookie_httponly, samesite=cookie_samesite)
    return response
