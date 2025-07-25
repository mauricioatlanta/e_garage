
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.inspeccion import Inspeccion
from taller.forms import InspeccionForm
from taller.models.perfilusuario import PerfilUsuario

@login_required
def listar_inspecciones(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        inspecciones = Inspeccion.objects.all()
    else:
        inspecciones = Inspeccion.objects.filter(empresa=perfil.empresa)
    return render(request, 'inspecciones/listar_inspecciones.html', {'inspecciones': inspecciones})

@login_required
def crear_inspeccion(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = InspeccionForm(request.POST)
        if form.is_valid():
            inspeccion = form.save(commit=False)
            inspeccion.empresa = perfil.empresa
            inspeccion.save()
            return redirect('inspecciones:listar_inspecciones')
    else:
        form = InspeccionForm()
    return render(request, 'inspecciones/crear_inspeccion.html', {'form': form})

@login_required
def detalle_inspeccion(request, inspeccion_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        inspeccion = get_object_or_404(Inspeccion, id=inspeccion_id)
    else:
        inspeccion = get_object_or_404(Inspeccion, id=inspeccion_id, empresa=perfil.empresa)
    return render(request, 'inspecciones/detalle_inspeccion.html', {'inspeccion': inspeccion})
