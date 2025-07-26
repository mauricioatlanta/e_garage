from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.compra import Compra
from taller.forms import CompraForm

@login_required
from taller.models.perfil_usuario import PerfilUsuario

@login_required
def listar_compras(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        compras = Compra.objects.all()
    else:
        compras = Compra.objects.filter(empresa=perfil.empresa)
    return render(request, 'compras/listar_compras.html', {'compras': compras})

@login_required
@login_required
def crear_compra(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.empresa = perfil.empresa
            compra.save()
            return redirect('compras:listar_compras')
    else:
        form = CompraForm()
    return render(request, 'compras/crear_compra.html', {'form': form})

@login_required
@login_required
def detalle_compra(request, compra_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        compra = get_object_or_404(Compra, id=compra_id)
    else:
        compra = get_object_or_404(Compra, id=compra_id, empresa=perfil.empresa)
    return render(request, 'compras/detalle_compra.html', {'compra': compra})
