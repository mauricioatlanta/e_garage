from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.solicitud import Solicitud
from taller.forms import SolicitudForm
from taller.models.perfil_usuario import PerfilUsuario

@login_required
def listar_solicitudes(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        solicitudes = Solicitud.objects.all()
    else:
        solicitudes = Solicitud.objects.filter(empresa=perfil.empresa)
    return render(request, 'solicitudes/listar_solicitudes.html', {'solicitudes': solicitudes})

@login_required
def crear_solicitud(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.empresa = perfil.empresa
            solicitud.save()
            return redirect('solicitudes:listar_solicitudes')
    else:
        form = SolicitudForm()
    return render(request, 'solicitudes/crear_solicitud.html', {'form': form})

@login_required
def detalle_solicitud(request, solicitud_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    else:
        solicitud = get_object_or_404(Solicitud, id=solicitud_id, empresa=perfil.empresa)
    return render(request, 'solicitudes/detalle_solicitud.html', {'solicitud': solicitud})
