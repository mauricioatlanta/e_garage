from django import template

register = template.Library()


@register.filter
def add_class(field, css_class):
    """Agregar clase CSS a un campo de formulario"""
    return field.as_widget(attrs={"class": css_class})
