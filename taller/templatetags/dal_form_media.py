# Template tag para cargar form.media (DAL/Select2) UNA SOLA VEZ por request.
# Evita el error "The DAL function 'select2' has already been registered"
# cuando form.media se incluye en varios niveles de la cadena de templates.

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

REQUEST_ATTR_CSS = "_eg_form_media_css_rendered"
REQUEST_ATTR_JS = "_eg_form_media_js_rendered"


@register.simple_tag(takes_context=True)
def form_media_once(context, form, kind="js"):
    """
    Renderiza form.media.css o form.media.js una sola vez por request.
    Uso: {% load dal_form_media %} ... {% form_media_once form 'css' %} ... {% form_media_once form 'js' %}
    """
    if form is None:
        return ""
    request = context.get("request")
    if request is None:
        # Sin request: comportarse como {{ form.media.css }} o {{ form.media.js }}
        if kind == "css":
            return form.media.render_css() if hasattr(form, "media") else ""
        return form.media.render_js() if hasattr(form, "media") else ""

    attr = REQUEST_ATTR_CSS if kind == "css" else REQUEST_ATTR_JS
    if getattr(request, attr, False):
        return ""

    setattr(request, attr, True)
    if not hasattr(form, "media"):
        return ""
    out = form.media.render_css() if kind == "css" else form.media.render_js()
    return mark_safe(out) if out else ""
