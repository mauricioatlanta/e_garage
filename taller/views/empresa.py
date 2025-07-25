from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..models.empresa import Empresa
from ..empresa_forms import EmpresaForm

@login_required
def editar_empresa(request):
    empresa, created = Empresa.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'empresa_form.html', {'form': form})
