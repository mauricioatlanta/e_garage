from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.venta import Venta
from taller.forms import VentaForm
from taller.models.perfil_usuario import PerfilUsuario

@login_required
def listar_ventas(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        ventas = Venta.objects.all()
    else:
        ventas = Venta.objects.filter(empresa=perfil.empresa)
    return render(request, 'ventas/listar_ventas.html', {'ventas': ventas})

@login_required
def crear_venta(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.empresa = perfil.empresa
            venta.save()
            return redirect('ventas:listar_ventas')
    else:
        form = VentaForm()
    return render(request, 'ventas/crear_venta.html', {'form': form})

@login_required
def detalle_venta(request, venta_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        venta = get_object_or_404(Venta, id=venta_id)
    else:
        venta = get_object_or_404(Venta, id=venta_id, empresa=perfil.empresa)
    return render(request, 'ventas/detalle_venta.html', {'venta': venta})
