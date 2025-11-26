from django import template

register = template.Library()


@register.filter
def add_class(field, css_class):
    """Agregar clase CSS a un campo de formulario"""
    return field.as_widget(attrs={"class": css_class})


@register.filter
def class_name(value):
    """Obtener el nombre de la clase de un objeto"""
    if value is None:
        return "None"
    return value.__class__.__name__


@register.filter
def is_numeric_only(value):
    """Verificar si un string contiene solo números"""
    if not value:
        return False
    return str(value).strip().isdigit()
