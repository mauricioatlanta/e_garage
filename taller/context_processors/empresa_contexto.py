from django.conf import settings
from django.core.cache import cache

from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa


def empresa_contexto(request):
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
                "empresa_actual": empresa,
                "empresa": empresa,  # Para compatibilidad
                "nombre_taller": empresa.nombre_taller,
                "logo_taller": logo_url,
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
