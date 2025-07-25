from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.mecanico import Mecanico
from taller.forms import DocumentoForm
from taller.models.perfilusuario import PerfilUsuario
import json

@login_required
def lista_documentos(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        documentos = Documento.objects.all()
    else:
        documentos = Documento.objects.filter(empresa=perfil.empresa)
    return render(request, 'taller/documentos/lista_documentos.html', {'documentos': documentos})

@login_required
def crear_documento(request):
    perfil = PerfilUsuario.objects.get(user=request.user)

    if request.method == 'POST':
        form = DocumentoForm(request.POST)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.empresa = perfil.empresa
            documento.save()

            # Procesar repuestos y servicios desde el campo json_items
            json_items = request.POST.get('json_items')
            print("[DEBUG] json_items recibido:", json_items)
            print("[DEBUG] Tipo de json_items:", type(json_items))
            print("[DEBUG] POST completo:", dict(request.POST))
            if json_items:
                try:
                    data = json.loads(json_items)
                    print(f"[DEBUG] Items a procesar: {len(data)}")
                    for index, item in enumerate(data):
                        print(f"[DEBUG] Procesando item {index+1}:", item)
                        if item['tipo'] == 'repuesto':
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item['partnumber'],
                                nombre=item['nombre'],
                                cantidad=item['cantidad'],
                                precio=item['precio'],
                            )
                            print(f"[DEBUG] Repuesto creado: {item['nombre']}")
                        elif item['tipo'] == 'servicio':
                            ServicioDocumento.objects.create(
                                empresa=perfil.empresa,
                                documento=documento,
                                nombre=item['nombre'],
                                precio=item['precio'],
                            )
                            print(f"[DEBUG] Servicio creado: {item['nombre']}")
                    
                    # Verificamos que los items se hayan guardado
                    repuestos = RepuestoDocumento.objects.filter(documento=documento)
                    servicios = ServicioDocumento.objects.filter(documento=documento)
                    print(f"[DEBUG] Repuestos guardados: {repuestos.count()}")
                    print(f"[DEBUG] Servicios guardados: {servicios.count()}")
                    
                except json.JSONDecodeError as e:
                    print("[ERROR] JSON inválido en json_items:", e)
            else:
                print("[DEBUG] No se recibió json_items o está vacío")

            return redirect('documentos:lista_documentos')
    else:
        form = DocumentoForm()

    # Cargar mecánicos activos del taller
    mecanicos = Mecanico.objects.filter(empresa=perfil.empresa, activo=True)

    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
        'mecanicos': mecanicos,
    })

@login_required
def editar_documento(request, documento_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        documento = get_object_or_404(Documento, id=documento_id)
    else:
        documento = get_object_or_404(Documento, id=documento_id, empresa=perfil.empresa)

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
                                empresa=perfil.empresa,
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
    mecanicos = Mecanico.objects.filter(empresa=perfil.empresa, activo=True)

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
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        documento = get_object_or_404(Documento, id=documento_id)
    else:
        documento = get_object_or_404(Documento, id=documento_id, empresa=perfil.empresa)
    return render(request, 'taller/documentos/detalle_documento.html', {'documento': documento})
