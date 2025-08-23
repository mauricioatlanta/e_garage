
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.repuesto import Repuesto
from taller.forms.repuesto import RepuestoForm
from taller.models.perfil_usuario import PerfilUsuario

@login_required
def lista_repuestos(request):
    # Mostrar solo repuestos del usuario
    repuestos = Repuesto.objects.filter(user=request.user)
    return render(request, 'repuestos/lista_repuestos.html', {'repuestos': repuestos})

@login_required
def crear_repuesto(request):
    if request.method == 'POST':
        form = RepuestoForm(request.POST)
        if form.is_valid():
            repuesto = form.save(commit=False)
            repuesto.user = request.user
            repuesto.save()
            return redirect('repuestos:lista_repuestos')
    else:
        form = RepuestoForm()
    return render(request, 'repuestos/crear_repuesto.html', {'form': form})

@login_required
def detalle_repuesto(request, repuesto_id):
    repuesto = get_object_or_404(Repuesto, id=repuesto_id, user=request.user)
    return render(request, 'repuestos/detalle_repuesto.html', {'repuesto': repuesto})
