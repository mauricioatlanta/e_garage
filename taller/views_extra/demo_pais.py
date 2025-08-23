from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from taller.utils.pais_utils import get_configuracion_pais, get_marcas_por_pais

@login_required
def demo_pais(request):
    """
    Vista de demostración para mostrar la funcionalidad por país
    """
    context = {}
    
    if hasattr(request.user, 'empresa'):
        empresa = request.user.empresa
        context.update({
            'empresa': empresa,
            'configuracion_pais': get_configuracion_pais(empresa),
            'marcas_disponibles': get_marcas_por_pais(request.user),
            'es_usa': empresa.pais == 'US',
            'es_chile': empresa.pais == 'CL',
        })
    
    return render(request, 'taller/demo_pais.html', context)
