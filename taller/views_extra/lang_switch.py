from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

ALLOWED_BY_COUNTRY = {"US": ("en", "es")}


@require_POST
@csrf_protect
def set_language_us(request):
    empresa = getattr(request, "empresa", None)
    if not empresa or empresa.pais != "US":
        messages.error(request, "Cambio de idioma no permitido para tu país.")
        return redirect(request.POST.get("next") or "/")

    lang = request.POST.get("language")
    if lang in ALLOWED_BY_COUNTRY["US"]:
        request.session["preferred_lang"] = lang
        messages.success(request, "Idioma actualizado.")
    else:
        messages.error(request, "Idioma no permitido.")

    return redirect(request.POST.get("next") or "/")
