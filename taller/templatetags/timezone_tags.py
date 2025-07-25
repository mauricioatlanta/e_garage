from django import template
from django.utils import timezone
import pytz

register = template.Library()

@register.filter
def local_datetime(value, empresa=None):
    """
    Convierte datetime a hora local del taller
    Uso: {{ documento.fecha_creacion|local_datetime:request.user.empresa }}
    """
    if not value or not empresa:
        return value
    
    try:
        return empresa.format_local_datetime(value, 'full')
    except:
        return value

@register.filter  
def local_date(value, empresa=None):
    """
    Convierte datetime a fecha local (solo fecha)
    Uso: {{ documento.fecha_creacion|local_date:request.user.empresa }}
    """
    if not value or not empresa:
        return value
    
    try:
        return empresa.format_local_datetime(value, 'date')
    except:
        return value

@register.filter
def local_time(value, empresa=None):
    """
    Convierte datetime a hora local (solo hora)
    Uso: {{ documento.fecha_creacion|local_time:request.user.empresa }}
    """
    if not value or not empresa:
        return value
    
    try:
        return empresa.format_local_datetime(value, 'time')
    except:
        return value

@register.filter
def local_short(value, empresa=None):
    """
    Convierte datetime a formato corto local
    Uso: {{ documento.fecha_creacion|local_short:request.user.empresa }}
    """
    if not value or not empresa:
        return value
    
    try:
        return empresa.format_local_datetime(value, 'short')
    except:
        return value

@register.simple_tag
def now_local(empresa):
    """
    Retorna la fecha/hora actual en zona horaria local
    Uso: {% now_local request.user.empresa %}
    """
    if not empresa:
        return timezone.now()
    
    try:
        return empresa.now_local()
    except:
        return timezone.now()

@register.inclusion_tag('taller/widgets/timezone_display.html')
def timezone_widget(empresa):
    """
    Widget para mostrar la zona horaria actual
    Uso: {% timezone_widget request.user.empresa %}
    """
    if not empresa:
        return {'timezone_display': 'UTC', 'current_time': timezone.now()}
    
    try:
        return {
            'timezone_display': empresa.timezone_display,
            'current_time': empresa.now_local(),
            'formatted_time': empresa.format_local_datetime(empresa.now_local(), 'full')
        }
    except:
        return {'timezone_display': 'UTC', 'current_time': timezone.now()}
