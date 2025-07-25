from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from taller.forms.empresa import EmpresaForm, DatosPersonalesForm
from taller.models.empresa import Empresa

@login_required
def configuracion(request):
    """Vista para configurar los datos de la empresa/taller y datos personales"""
    # Obtener o crear la empresa del usuario actual
    empresa, created = Empresa.objects.get_or_create(usuario=request.user)
    
    # Inicializar formularios
    empresa_form = EmpresaForm(instance=empresa)
    datos_form = DatosPersonalesForm(user=request.user)
    
    if request.method == 'POST':
        # Determinar qué formulario se envió
        if 'empresa_form' in request.POST:
            empresa_form = EmpresaForm(request.POST, request.FILES, instance=empresa)
            
            if empresa_form.is_valid():
                empresa_form.save()
                messages.success(request, '✅ Datos de la empresa actualizados correctamente!')
                return redirect('configuracion')
            else:
                messages.error(request, '❌ Error al guardar los datos de la empresa. Revisa los datos.')
        
        elif 'datos_form' in request.POST:
            datos_form = DatosPersonalesForm(request.POST, user=request.user)
            
            if datos_form.is_valid():
                # Actualizar datos del usuario
                user = request.user
                user.first_name = datos_form.cleaned_data['first_name']
                user.last_name = datos_form.cleaned_data['last_name']
                user.email = datos_form.cleaned_data['email']
                user.save()
                
                messages.success(request, '✅ Datos personales actualizados correctamente!')
                return redirect('configuracion')
            else:
                messages.error(request, '❌ Error al guardar los datos personales. Revisa los datos.')

    context = {
        'empresa_form': empresa_form,
        'datos_form': datos_form,
        'empresa': empresa,
        'created': created
    }
    return render(request, 'taller/configuracion.html', context)
