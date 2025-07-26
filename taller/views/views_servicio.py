
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.documento import ServicioDocumento
from taller.forms import ServicioForm
from taller.models.perfil_usuario import PerfilUsuario

@login_required
def lista_servicios(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        servicios = ServicioDocumento.objects.all()
    else:
        servicios = ServicioDocumento.objects.filter(empresa=perfil.empresa)
    return render(request, 'servicios/lista_servicios.html', {'servicios': servicios})

@login_required
def crear_servicio(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.empresa = perfil.empresa
            servicio.save()
            return redirect('servicios:lista_servicios')
    else:
        form = ServicioForm()
    return render(request, 'servicios/crear_servicio.html', {'form': form})

@login_required
def detalle_servicio(request, servicio_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        servicio = get_object_or_404(ServicioDocumento, id=servicio_id)
    else:
        servicio = get_object_or_404(ServicioDocumento, id=servicio_id, empresa=perfil.empresa)
    return render(request, 'servicios/detalle_servicio.html', {'servicio': servicio})
