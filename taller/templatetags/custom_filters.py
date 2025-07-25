from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter
def formatear_pesos(valor):
    try:
        valor = int(valor)
        return "${:,.0f}".format(valor).replace(",", ".")
    except (ValueError, TypeError):
        return valor

@register.filter
def formatear_pesos_compacto(valor):
    """
    Formatea números grandes de manera compacta para KPIs.
    Ejemplo: 10181720 -> $10.2M
    """
    try:
        valor = float(valor)
        if valor >= 1000000000:
            return f"${valor/1000000000:.1f}B"
        elif valor >= 1000000:
            return f"${valor/1000000:.1f}M"
        elif valor >= 1000:
            return f"${valor/1000:.0f}K"
        else:
            return f"${valor:.0f}"
    except (ValueError, TypeError):
        return valor

@register.filter
def sumar_campo(lista, campo):
    """
    Suma los valores de un campo específico en una lista de diccionarios.
    Uso: {{ resultados|sumar_campo:'total_ganancia' }}
    """
    return sum(item.get(campo, 0) or 0 for item in lista)

@register.filter(name='add_class')
def add_class(field, css_class):
    if isinstance(field, BoundField):  # Verifica si el objeto es un campo de formulario
        return field.as_widget(attrs={"class": css_class})
    return field  # Devuelve el valor original si no es un campo de formulario