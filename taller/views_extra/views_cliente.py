
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from taller.models.clientes import Cliente
from taller.forms.clientes import ClienteForm

@login_required
def lista_clientes(request):
    clientes = Cliente.objects.filter(user=request.user)
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes})

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.user = request.user
            cliente.save()
            return redirect('clientes:lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/crear_cliente.html', {'form': form})

@login_required
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id, user=request.user)
    return render(request, 'clientes/detalle_cliente.html', {'cliente': cliente})
