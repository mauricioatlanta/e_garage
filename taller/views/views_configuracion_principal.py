from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from taller.models.perfilusuario import PerfilUsuario
from taller.models.mecanico import Mecanico

@login_required
def configuracion_principal(request):
    """
    Vista principal de configuración del taller
    """
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
        
        # Estadísticas rápidas (con manejo de errores)
        total_mecanicos = Mecanico.objects.filter(empresa=empresa).count()
        mecanicos_activos = Mecanico.objects.filter(empresa=empresa, activo=True).count()
        mecanicos_inactivos = total_mecanicos - mecanicos_activos
        
    except PerfilUsuario.DoesNotExist:
        # Si no tiene perfil, crear datos por defecto
        empresa = None
        total_mecanicos = 0
        mecanicos_activos = 0
        mecanicos_inactivos = 0
    
    context = {
        'empresa': empresa,
        'stats': {
            'total_mecanicos': total_mecanicos,
            'mecanicos_activos': mecanicos_activos,
            'mecanicos_inactivos': mecanicos_inactivos,
        }
    }
    
    return render(request, 'taller/configuracion/principal.html', context)
