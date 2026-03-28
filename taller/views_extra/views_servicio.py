from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from taller.forms import ServicioForm
from taller.templatetags.country_url import reverse_country_url
from taller.models.lineas_documento import LineaServicio
from taller.models.perfil_usuario import PerfilUsuario


@login_required
def lista_servicios(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        servicios = LineaServicio.objects.all()
    else:
        servicios = LineaServicio.objects.filter(documento__empresa=perfil.empresa)
    return render(request, "servicios/lista_servicios.html", {"servicios": servicios})


@login_required
def crear_servicio(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == "POST":
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.empresa = perfil.empresa
            servicio.save()
            return redirect(reverse_country_url(request, "servicios:servicios_menu"))
    else:
        form = ServicioForm()
    return render(request, "servicios/crear_servicio.html", {"form": form})


@login_required
def detalle_servicio(request, servicio_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        servicio = get_object_or_404(LineaServicio, id=servicio_id)
    else:
        servicio = get_object_or_404(
            LineaServicio, id=servicio_id, documento__empresa=perfil.empresa
        )
    return render(request, "servicios/detalle_servicio.html", {"servicio": servicio})
