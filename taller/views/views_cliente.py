
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.clientes import Cliente
from taller.models.perfilusuario import PerfilUsuario

@login_required
def lista_clientes(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(empresa=perfil.empresa)
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes})

@login_required
def crear_cliente(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.empresa = perfil.empresa
            cliente.save()
            return redirect('clientes:lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/crear_cliente.html', {'form': form})

@login_required
def detalle_cliente(request, cliente_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    else:
        cliente = get_object_or_404(Cliente, id=cliente_id, empresa=perfil.empresa)
    return render(request, 'clientes/detalle_cliente.html', {'cliente': cliente})
