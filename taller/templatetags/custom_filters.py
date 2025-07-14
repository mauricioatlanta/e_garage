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