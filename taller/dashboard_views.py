from django.shortcuts import render, redirect
from taller.models.vehiculos import Vehiculo
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    # Si es superusuario, redirigir al admin
    if request.user.is_superuser:
        return redirect('/admin/')
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    # Filtrar vehículos solo de la empresa del usuario
    vehiculos = Vehiculo.objects.filter(empresa=empresa).select_related('marca', 'modelo', 'cliente').order_by('-id')[:5]
    
    return render(request, 'taller/dashboard.html', {
        'vehiculos': vehiculos,
        'empresa': empresa
    })
