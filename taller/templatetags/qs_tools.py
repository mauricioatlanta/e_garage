from django import template
register = template.Library()

@register.filter
def qs_count(value):
    """Cuenta elementos en un queryset o relación para diagnóstico"""
    try:
        return value.count()
    except Exception:
        return 0
