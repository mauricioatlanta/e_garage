import os
from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()

_PLACEHOLDER = "img/welcome/scenes/placeholder.webp"


@register.simple_tag
def scene_image(path):
    """Return the static URL for a scene image, falling back to placeholder.webp.

    Usage in templates:
        {% load welcome_tags %}
        {% scene_image scene.image as src %}
        <img src="{{ src }}">
    """
    if not path:
        return static(_PLACEHOLDER)
    abs_path = os.path.join(settings.BASE_DIR, "static", path)
    if not os.path.exists(abs_path):
        path = _PLACEHOLDER
    return static(path)
