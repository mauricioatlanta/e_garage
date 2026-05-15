from django import template

register = template.Library()


@register.filter
def replace_spaces_with_hyphens(value):
    """Reemplaza espacios con guiones para nombres de clases CSS"""
    return value.replace(" ", "-").lower()
