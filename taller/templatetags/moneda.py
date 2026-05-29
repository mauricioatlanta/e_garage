from django import template

register = template.Library()


@register.filter
def clp(value):
    try:
        n = int(round(float(value)))
    except Exception:
        return value
    s = f"{n:,}".replace(",", ".")
    return f"${s}"
