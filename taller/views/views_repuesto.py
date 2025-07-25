
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.repuesto import Repuesto
from taller.forms.repuesto import RepuestoForm
from taller.models.perfilusuario import PerfilUsuario

def lista_repuestos(request):

@login_required
def lista_repuestos(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        repuestos = Repuesto.objects.all()
    else:
        repuestos = Repuesto.objects.filter(empresa=perfil.empresa)
    return render(request, 'repuestos/lista_repuestos.html', {'repuestos': repuestos})

def crear_repuesto(request):

@login_required
def crear_repuesto(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = RepuestoForm(request.POST)
        if form.is_valid():
            repuesto = form.save(commit=False)
            repuesto.empresa = perfil.empresa
            repuesto.save()
            return redirect('repuestos:lista_repuestos')
    else:
        form = RepuestoForm()
    return render(request, 'repuestos/crear_repuesto.html', {'form': form})

def detalle_repuesto(request, repuesto_id):

@login_required
def detalle_repuesto(request, repuesto_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        repuesto = get_object_or_404(Repuesto, id=repuesto_id)
    else:
        repuesto = get_object_or_404(Repuesto, id=repuesto_id, empresa=perfil.empresa)
    return render(request, 'repuestos/detalle_repuesto.html', {'repuesto': repuesto})
