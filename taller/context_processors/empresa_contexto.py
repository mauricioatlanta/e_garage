from taller.models.empresa import Empresa
from django.core.cache import cache
from django.conf import settings
from taller.models import CompanySettings

def empresa_contexto(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            empresa = Empresa.objects.get(user=user)
            return {
                'empresa': empresa,
                'nombre_taller': empresa.nombre_taller,
                'logo_taller': empresa.logo.url if empresa.logo else None,
            }
        except Empresa.DoesNotExist:
            return {
                'empresa': None,
                'nombre_taller': 'eGarage',
                'logo_taller': None,
            }
    return {
        'empresa': None,
        'nombre_taller': 'eGarage',
        'logo_taller': None,
    }
