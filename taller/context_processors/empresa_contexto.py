from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa


def empresa_contexto(request):
    """
    Context processor mejorado para exponer datos de Empresa en todas las plantillas.
    Incluye estado de suscripción, moneda, alertas y más funcionalidades del modelo refinado.
    """
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        try:
            empresa = Empresa.objects.get(user=user)

            # Buscar configuración
            logo_url = None
            try:
                config = ConfiguracionEmpresa.objects.get(empresa=empresa)
                logo_url = config.logo.url if config.logo else None
            except ConfiguracionEmpresa.DoesNotExist:
                logo_url = empresa.logo.url if empresa.logo else None

            return {
                # Compatibilidad con código existente
                "empresa_actual": empresa,
                "empresa": empresa,
                "nombre_taller": empresa.nombre_taller,
                "logo_taller": logo_url,
                
                # Nuevas funcionalidades del modelo refinado
                "empresa_nombre": empresa.nombre_taller,
                "empresa_logo": empresa.logo.url if empresa.logo else None,
                "empresa_pais": empresa.pais,
                "empresa_moneda": empresa.formato_moneda,  # dict con simbolo, codigo, decimales
                "empresa_estado_suscripcion": empresa.estado_suscripcion,
                "empresa_color_estado": empresa.color_estado,
                "empresa_dias_restantes": empresa.dias_restantes,
                "empresa_debe_mostrar_alerta": empresa.debe_mostrar_alerta(),
                "empresa_mensaje_alerta": empresa.get_mensaje_alerta(),
                "empresa_fecha_expiracion": empresa.fecha_expiracion,
                "empresa_now_local": empresa.now_local(),
                "empresa_timezone_display": empresa.timezone_display,
            }
        except Empresa.DoesNotExist:
            return {
                "empresa_actual": None,
                "empresa": None,
                "nombre_taller": "eGarage",
                "logo_taller": None,
            }
    return {
        "empresa_actual": None,
        "empresa": None,
        "nombre_taller": "eGarage",
        "logo_taller": None,
    }
