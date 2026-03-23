# Template tag para cargar form.media (DAL/Select2) UNA SOLA VEZ por request.
# Evita el error "The DAL function 'select2' has already been registered"
# cuando form.media se incluye en varios niveles de la cadena de templates.

from itertools import chain

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

REQUEST_ATTR_CSS = "_eg_form_media_css_rendered"
REQUEST_ATTR_JS = "_eg_form_media_js_rendered"


def _normalize_media_output(out):
    """
    Django 5 puede devolver list (render_js) o iterator/chain (render_css).
    Convertir siempre a HTML string real, no repr() de lista/iterable.
    """
    if not out:
        return ""
    if isinstance(out, str):
        return out
    if isinstance(out, (list, tuple)):
        return "\n".join(str(x) for x in out)
    if isinstance(out, chain) or hasattr(out, "__iter__"):
        return "\n".join(str(x) for x in out)
    return str(out)


@register.simple_tag(takes_context=True)
def form_media_once(context, form, kind="js"):
    """
    Renderiza form.media.css o form.media.js una sola vez por request.
    Uso:
        {% load dal_form_media %}
        {% form_media_once form 'css' %}
        {% form_media_once form 'js' %}
    """
    if form is None or not hasattr(form, "media"):
        return ""

    if kind == "css":
        out = form.media.render_css()
        attr = REQUEST_ATTR_CSS
    else:
        out = form.media.render_js()
        attr = REQUEST_ATTR_JS

    request = context.get("request")
    if request is None:
        out = _normalize_media_output(out)
        return mark_safe(out) if out else ""

    if getattr(request, attr, False):
        return ""

    setattr(request, attr, True)
    out = _normalize_media_output(out)
    return mark_safe(out) if out else ""
