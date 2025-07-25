from django.utils import timezone
import pytz

class TimezoneHelper:
    """
    Helper para manejo de zonas horarias en el sistema
    """
    
    @staticmethod
    def get_empresa_now(empresa):
        """
        Retorna datetime actual en la zona horaria de la empresa
        Para usar al crear documentos: fecha_creacion = TimezoneHelper.get_empresa_now(empresa)
        """
        if not empresa or not hasattr(empresa, 'zona_horaria'):
            return timezone.now()
        
        try:
            return empresa.now_local()
        except:
            return timezone.now()
    
    @staticmethod
    def convert_to_empresa_timezone(dt, empresa):
        """
        Convierte cualquier datetime a la zona horaria de la empresa
        """
        if not empresa or not hasattr(empresa, 'zona_horaria'):
            return dt
        
        try:
            return empresa.convert_to_local_time(dt)
        except:
            return dt
    
    @staticmethod
    def format_for_empresa(dt, empresa, format_type='full'):
        """
        Formatea datetime para mostrar en la zona horaria de la empresa
        """
        if not empresa or not hasattr(empresa, 'zona_horaria'):
            return dt.strftime("%m/%d/%Y – %I:%M %p") if dt else ""
        
        try:
            return empresa.format_local_datetime(dt, format_type)
        except:
            return dt.strftime("%m/%d/%Y – %I:%M %p") if dt else ""

# Función helper para usar en vistas
def get_empresa_timezone_now(request):
    """
    Helper function para obtener la hora actual en timezone de la empresa del usuario
    Uso en vistas: documento.fecha_creacion = get_empresa_timezone_now(request)
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            empresa = request.user.empresa
            return TimezoneHelper.get_empresa_now(empresa)
        except:
            pass
    
    return timezone.now()
