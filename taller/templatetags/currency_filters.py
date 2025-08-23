from django import template
from django.template.defaultfilters import floatformat
from decimal import Decimal
import locale

register = template.Library()

@register.filter
def currency_format(value, country_code='US'):
    """
    Formatea valores monetarios según el país:
    - US: $2,000.25
    - CL: $2.000 (sin decimales)
    """
    if value is None:
        return "$0"
    
    try:
        # Convertir a Decimal si no lo es
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        if country_code == 'US':
            # Formato US: $2,000.25
            return f"${value:,.2f}"
        else:
            # Formato CL: $2.000 (sin decimales)
            return f"${value:,.0f}".replace(',', '.')
    except (ValueError, TypeError):
        return "$0"

@register.filter
def mileage_label(country_code, language='es'):
    """
    Retorna la etiqueta correcta para kilometraje/millas según país e idioma:
    - US + es: Millas
    - US + en: Miles  
    - CL + cualquier: Kilometraje
    """
    if country_code == 'US':
        return 'Miles' if language == 'en' else 'Millas'
    else:
        return 'Kilometraje'
