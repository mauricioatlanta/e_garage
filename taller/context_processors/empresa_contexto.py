import logging

from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa

logger = logging.getLogger(__name__)

_EMPTY = {
    "empresa_actual": None,
    "empresa": None,
    "nombre_taller": "eGarage",
    "logo_taller": None,
    "empresa_pais": "CL",
}


def empresa_contexto(request):
    """
    Context processor mejorado para exponer datos de Empresa en todas las plantillas.
    Nunca debe lanzar: ante cualquier error retorna valores seguros para evitar 500.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return _EMPTY.copy()

    try:
        empresa = Empresa.objects.get(user=user)
    except Empresa.DoesNotExist:
        try:
            empresa = Empresa.objects.filter(usuario=user).first()
        except Exception:
            return _EMPTY.copy()
        if not empresa:
            return _EMPTY.copy()
    except Exception as e:
        logger.warning("empresa_contexto: error obteniendo empresa: %s", e)
        return _EMPTY.copy()

    try:
        logo_url = None
        try:
            config = ConfiguracionEmpresa.objects.get(empresa=empresa)
            logo_url = config.logo.url if getattr(config, "logo", None) else None
        except ConfiguracionEmpresa.DoesNotExist:
            logo_url = empresa.logo.url if getattr(empresa, "logo", None) else None
        except Exception:
            logo_url = getattr(empresa, "logo", None)
            logo_url = logo_url.url if logo_url else None

        result = {
            "empresa_actual": empresa,
            "empresa": empresa,
            "nombre_taller": getattr(empresa, "nombre_taller", "eGarage"),
            "logo_taller": logo_url,
            "empresa_nombre": getattr(empresa, "nombre_taller", "eGarage"),
            "empresa_logo": empresa.logo.url if getattr(empresa, "logo", None) else None,
            "empresa_pais": getattr(empresa, "pais", "CL"),
        }
        # Atributos opcionales del modelo refinado (pueden no existir en todas las instalaciones)
        for key, attr in [
            ("empresa_moneda", "formato_moneda"),
            ("empresa_estado_suscripcion", "estado_suscripcion"),
            ("empresa_color_estado", "color_estado"),
            ("empresa_dias_restantes", "dias_restantes"),
            ("empresa_fecha_expiracion", "fecha_expiracion"),
        ]:
            if hasattr(empresa, attr):
                result[key] = getattr(empresa, attr)
        if hasattr(empresa, "debe_mostrar_alerta") and callable(empresa.debe_mostrar_alerta):
            result["empresa_debe_mostrar_alerta"] = empresa.debe_mostrar_alerta()
        if hasattr(empresa, "get_mensaje_alerta") and callable(empresa.get_mensaje_alerta):
            result["empresa_mensaje_alerta"] = empresa.get_mensaje_alerta()
        if hasattr(empresa, "now_local") and callable(empresa.now_local):
            result["empresa_now_local"] = empresa.now_local()
        if hasattr(empresa, "timezone_display"):
            result["empresa_timezone_display"] = empresa.timezone_display
        return result
    except Exception as e:
        logger.warning("empresa_contexto: error construyendo contexto: %s", e)
        return {
            **_EMPTY,
            "empresa_actual": empresa,
            "empresa": empresa,
            "nombre_taller": getattr(empresa, "nombre_taller", "eGarage"),
            "empresa_pais": getattr(empresa, "pais", "CL"),
        }
