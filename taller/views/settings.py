from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..forms.settings import ConfigEmpresaForm
from ..models import ConfiguracionEmpresa, Tecnico

def es_staff(user):
    return user.is_staff

@login_required
@user_passes_test(es_staff)
def ver_configuracion(request):
    """Vista para ver la configuración de la empresa"""
    try:
        cfg = request.user.empresa.config
    except ConfiguracionEmpresa.DoesNotExist:
        # Crear configuración si no existe
        cfg = ConfiguracionEmpresa.objects.create(empresa=request.user.empresa)
    
    # Obtener técnicos de la empresa
    tecnicos = Tecnico.objects.filter(empresa=request.user.empresa)
    
    context = {
        'cfg': cfg,
        'tecnicos': tecnicos,
    }
    return render(request, 'taller/settings/config_detail.html', context)

@login_required
@user_passes_test(es_staff)
def ajustar_configuracion(request):
    """Vista para editar la configuración de la empresa"""
    try:
        cfg = request.user.empresa.config
    except ConfiguracionEmpresa.DoesNotExist:
        # Crear configuración si no existe
        cfg = ConfiguracionEmpresa.objects.create(empresa=request.user.empresa)
    
    if request.method == 'POST':
        form = ConfigEmpresaForm(request.POST, request.FILES, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada correctamente.')
            return redirect('taller:settings:ver_configuracion')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ConfigEmpresaForm(instance=cfg)
    
    context = {
        'form': form,
        'cfg': cfg,
    }
    return render(request, 'taller/settings/config_form.html', context)
