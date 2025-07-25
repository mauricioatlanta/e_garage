# Inyecta logo y nombre del taller automáticamente en el contexto de todas las vistas
from taller.models.empresa import Empresa

def empresa_contexto(request):
    if request.user.is_authenticated:
        try:
            empresa = Empresa.objects.get(user=request.user)
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
