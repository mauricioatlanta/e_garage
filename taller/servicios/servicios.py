from django.shortcuts import render, redirect, get_object_or_404
from taller.servicios.models import CategoriaServicio, SubcategoriaServicio
from taller.forms.servicios import ServicioForm 



def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('taller:explorador_servicios')
    else:
        form = ServicioForm()
    return render(request, 'taller/servicios/crear_servicio.html', {'form': form})

def editar_servicio(request, servicio_id):
    servicio = get_object_or_404(CategoriaServicio, id=servicio_id)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            return redirect('taller:explorador_servicios')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'taller/servicios/editar_servicio.html', {'form': form})

def eliminar_servicio(request, servicio_id):
    servicio = get_object_or_404(CategoriaServicio, id=servicio_id)
    if request.method == 'POST':
        servicio.delete()
        return redirect('taller:explorador_servicios')
    return render(request, 'taller/servicios/eliminar_servicio_confirmar.html', {'object': servicio})

def lista_servicios(request):
    categorias = CategoriaServicio.objects.prefetch_related('subcategorias__servicio_set').all()
    return render(request, 'taller/servicios/lista_servicios.html', {'categorias': categorias})

def explorador_servicios(request):
    categorias = CategoriaServicio.objects.prefetch_related('subcategorias__servicios').all()
    return render(request, 'taller/servicios/explorador_servicios.html', {
        'categorias': categorias
    })