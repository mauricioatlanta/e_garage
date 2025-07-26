from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.mecanico import Mecanico
from taller.forms import DocumentoForm
from taller.models.perfil_usuario import PerfilUsuario
import json

@login_required
def lista_documentos(request):
    # Mostrar solo documentos del usuario
    documentos = Documento.objects.filter(user=request.user)
    return render(request, 'taller/documentos/lista_documentos.html', {'documentos': documentos})

@login_required
def crear_documento(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.user = request.user
            documento.save()

            # Procesar repuestos y servicios desde el campo json_items
            json_items = request.POST.get('json_items')
            if json_items:
                try:
                    data = json.loads(json_items)
                    for item in data:
                        if item['tipo'] == 'repuesto':
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item['partnumber'],
                                nombre=item['nombre'],
                                cantidad=item['cantidad'],
                                precio=item['precio'],
                            )
                        elif item['tipo'] == 'servicio':
                            ServicioDocumento.objects.create(
                                documento=documento,
                                nombre=item['nombre'],
                                precio=item['precio'],
                            )
                    # Verificamos que los items se hayan guardado
                    # repuestos = RepuestoDocumento.objects.filter(documento=documento)
                    # servicios = ServicioDocumento.objects.filter(documento=documento)
                except json.JSONDecodeError:
                    pass
            return redirect('documentos:lista_documentos')
    else:
        form = DocumentoForm()

    # Cargar mecánicos activos del taller
    mecanicos = Mecanico.objects.filter(activo=True)

    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
        'mecanicos': mecanicos,
    })

@login_required
def editar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id, user=request.user)

    repuestos = RepuestoDocumento.objects.filter(documento=documento)
    servicios = ServicioDocumento.objects.filter(documento=documento)
    form = DocumentoForm(instance=documento)
    if request.method == 'POST':
        form = DocumentoForm(request.POST, instance=documento)
        if form.is_valid():
            form.save()
            # Procesar repuestos y servicios actualizados
            json_items = request.POST.get('json_items')
            if json_items:
                try:
                    data = json.loads(json_items)
                    # Eliminar ítems anteriores
                    RepuestoDocumento.objects.filter(documento=documento).delete()
                    ServicioDocumento.objects.filter(documento=documento).delete()
                    for item in data:
                        if item['tipo'] == 'repuesto':
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item['partnumber'],
                                nombre=item['nombre'],
                                cantidad=item['cantidad'],
                                precio=item['precio'],
                            )
                        elif item['tipo'] == 'servicio':
                            ServicioDocumento.objects.create(
                                documento=documento,
                                nombre=item['nombre'],
                                precio=item['precio'],
                            )
                    # Recargar repuestos y servicios después de guardar
                    repuestos = RepuestoDocumento.objects.filter(documento=documento)
                    servicios = ServicioDocumento.objects.filter(documento=documento)
                except json.JSONDecodeError:
                    pass
            return redirect('documentos:detalle_documento', documento_id=documento.pk)
    # Cargar mecánicos activos del taller
    mecanicos = Mecanico.objects.filter(activo=True)
    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
        'editando': True,
        'documento': documento,
        'repuestos': repuestos,
        'servicios': servicios,
        'mecanicos': mecanicos,
    })

@login_required
def detalle_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id, user=request.user)
    return render(request, 'taller/documentos/detalle_documento.html', {'documento': documento})
