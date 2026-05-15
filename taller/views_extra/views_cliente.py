from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from taller.forms.clientes import ClienteForm
from taller.models.clientes import Cliente


@login_required
def lista_clientes(request):
    # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
    # Nota: Este archivo parece usar campo legacy 'user'. Debe migrar a 'empresa'
    empresa = getattr(request.user, "empresa", None)
    if empresa:
        clientes = Cliente.objects.filter(empresa=empresa)
    else:
        clientes = Cliente.objects.none()
    return render(request, "clientes/lista_clientes.html", {"clientes": clientes})


@login_required
def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.user = request.user
            cliente.save()
            return redirect("taller:clientes:lista_clientes")
    else:
        form = ClienteForm()
    return render(request, "clientes/crear_cliente.html", {"form": form})


@login_required
def detalle_cliente(request, cliente_id):
    # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
    empresa = getattr(request.user, "empresa", None)
    if empresa:
        cliente = get_object_or_404(Cliente, id=cliente_id, empresa=empresa)
    else:
        from django.http import Http404

        raise Http404("Cliente no encontrado")
    return render(request, "clientes/detalle_cliente.html", {"cliente": cliente})
