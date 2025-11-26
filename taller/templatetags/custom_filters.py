import re

from django import template
from django.forms.boundfield import BoundField

register = template.Library()


@register.filter(name="sin_pais")
def sin_pais(value):
    """
    Elimina cualquier sufijo ' (País)' al final de la cadena, sin importar el país ni mayúsculas/minúsculas.
    Ejemplo: 'Cadillac (Chile)' -> 'Cadillac', 'Ford (USA)' -> 'Ford'
    """
    if not isinstance(value, str):
        return value
    return re.sub(r"\s*\([^)]+\)$", "", value).strip()


@register.filter
def formatear_pesos(valor):
    try:
        valor = int(valor)
        return f"${valor:,.0f}".replace(",", ".")
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


@register.filter(name="add_class")
def add_class(field, css_class):
    if isinstance(field, BoundField):  # Verifica si el objeto es un campo de formulario
        return field.as_widget(attrs={"class": css_class})
    return field  # Devuelve el valor original si no es un campo de formulario


@register.filter(name="add_thousands_separator")
def add_thousands_separator(value):
    """
    Agrega separadores de miles a un número.
    Ejemplo: 1234567 -> 1.234.567
    """
    try:
        # Convertir a entero si es posible
        if isinstance(value, (int, float)):
            num = int(value)
        else:
            num = int(float(str(value)))

        # Formatear con separadores de miles usando punto
        return f"{num:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value


@register.filter
def currency_format(value, country_code="US"):
    """
    Formatea valores monetarios según el país usando configuración centralizada.

    Soporta todos los países: US, CL, MX, PE, CO, EC, BR, VE

    Args:
        value: Monto a formatear
        country_code: Código de país (ISO 3166-1 alpha-2)

    Returns:
        str: Monto formateado según reglas del país
    """
    from taller.utils.country_config import format_currency

    if value is None:
        return "$0"

    try:
        return format_currency(value, country_code, include_symbol=True)
    except (ValueError, TypeError, Exception):
        return "$0"


@register.filter
def mileage_label(country_code, language="es"):
    """
    Retorna la etiqueta correcta para kilometraje/millas según país e idioma:
    - US + es: Millas
    - US + en: Miles
    - CL + cualquier: Kilometraje
    """
    if country_code == "US":
        return "Miles" if language == "en" else "Millas"
    else:
        return "Kilometraje"
