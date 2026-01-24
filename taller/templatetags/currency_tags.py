"""
Template tags para formateo de monedas según el país detectado.
Proporciona formateo automático de monedas que se adapta al país del usuario.
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def format_currency(context, amount):
    """
    Formatea un monto como moneda según el país detectado en el request.
    
    Args:
        context: Contexto del template (debe incluir 'request')
        amount: Monto a formatear (puede ser int, float, string o None)
    
    Returns:
        String formateado según el país:
        - CL: $ 45.000 (sin decimales, punto como separador de miles)
        - BR: R$ 45,00 (2 decimales, coma como separador decimal)
        - US: $ 45.00 (2 decimales, punto como separador decimal)
        - MX: $ 45.00 (2 decimales, punto como separador decimal)
    
    Example:
        {% load currency_tags %}
        <p>Total: {% format_currency orden.total %}</p>
    """
    request = context.get('request')
    if not request:
        # Fallback si no hay request
        return f"${float(amount or 0):,.0f}"
    
    country = getattr(request, 'country', 'CL').upper()
    
    # Configuración por país
    formats = {
        'CL': {
            'symbol': '$',
            'decimal_pos': 0,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
        'US': {
            'symbol': '$',
            'decimal_pos': 2,
            'thousand_sep': ',',
            'decimal_sep': '.'
        },
        'BR': {
            'symbol': 'R$',
            'decimal_pos': 2,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
        'MX': {
            'symbol': '$',
            'decimal_pos': 2,
            'thousand_sep': ',',
            'decimal_sep': '.'
        },
        'CO': {
            'symbol': '$',
            'decimal_pos': 0,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
        'AR': {
            'symbol': '$',
            'decimal_pos': 2,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
        'PE': {
            'symbol': 'S/',
            'decimal_pos': 2,
            'thousand_sep': ',',
            'decimal_sep': '.'
        },
        'EC': {
            'symbol': '$',
            'decimal_pos': 2,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
        'VE': {
            'symbol': 'Bs.',
            'decimal_pos': 2,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
        'UY': {
            'symbol': '$',
            'decimal_pos': 2,
            'thousand_sep': '.',
            'decimal_sep': ','
        },
    }
    
    # Obtener configuración o usar default
    config = formats.get(country, formats['CL'])
    
    # Convertir a float
    try:
        amount = float(amount or 0)
    except (ValueError, TypeError):
        amount = 0.0
    
    # Formatear número según el país
    # Python formatea con coma para miles y punto para decimales por defecto
    if config['decimal_pos'] == 0:
        # Sin decimales - formatear como entero con separadores de miles
        integer_amount = int(amount)
        number_str = f"{integer_amount:,}"  # Resultado: "1,234" o "1234"
    else:
        # Con decimales
        number_str = f"{amount:,.{config['decimal_pos']}f}"  # Resultado: "1,234.56" o "1234.56"
    
    # Ajustar separadores según el formato del país
    if config['thousand_sep'] == '.' and config['decimal_sep'] == ',':
        # Formato latino: 1.234.567,89
        # Necesitamos convertir: coma (miles) → punto, punto (decimal) → coma
        if '.' in number_str:
            # Tiene punto decimal - dividir por el último punto (que es el separador decimal)
            parts = number_str.rsplit('.', 1)
            if len(parts) == 2:
                integer_part, decimal_part = parts
                # Cambiar comas (separador de miles) por puntos
                integer_part = integer_part.replace(',', '.')
                formatted_number = f"{integer_part},{decimal_part}"
            else:
                formatted_number = number_str.replace(',', '.')
        else:
            # Solo parte entera - cambiar comas por puntos
            formatted_number = number_str.replace(',', '.')
    elif config['thousand_sep'] == ',' and config['decimal_sep'] == '.':
        # Formato inglés/US: 1,234,567.89 (Python ya hace esto correctamente)
        formatted_number = number_str
    else:
        # Usar formato por defecto
        formatted_number = number_str
    
    return f"{config['symbol']} {formatted_number}"


@register.filter
def currency(value, country_code='CL'):
    """
    Filtro simple para formatear moneda (versión simplificada del tag).
    
    Args:
        value: Monto a formatear
        country_code: Código de país (CL, BR, US, etc.)
    
    Returns:
        String formateado
    
    Example:
        {{ orden.total|currency:"BR" }}
    """
    # Mapeo simplificado
    symbols = {
        'BR': 'R$',
        'US': '$',
        'MX': '$',
        'PE': 'S/',
        'VE': 'Bs.',
    }
    
    symbol = symbols.get(country_code.upper(), '$')
    
    try:
        amount = float(value or 0)
        if country_code.upper() in ['CL', 'CO']:
            return f"{symbol} {int(amount):,}".replace(',', '.')
        else:
            return f"{symbol} {amount:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol} 0"

