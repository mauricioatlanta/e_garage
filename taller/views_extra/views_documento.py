from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio, LineaRepuesto
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
from taller.forms import DocumentoForm
from taller.models.perfil_usuario import PerfilUsuario
import json

@login_required
def lista_documentos(request):
    # Mostrar solo documentos de la empresa del usuario
    try:
        empresa = request.user.empresa
        from django.db.models import Sum, F, Value, DecimalField
        from django.db.models.functions import Coalesce
        
        documentos = (
            Documento.objects
            .filter(empresa=empresa)
            .select_related('cliente', 'vehiculo')  # Optimización para FKs
            .annotate(
                sum_rep=Coalesce(
                    Sum(
                        F('lineas_repuesto__cantidad') * F('lineas_repuesto__precio_unitario') * (1 - F('lineas_repuesto__descuento') / 100),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                ),
                sum_serv=Coalesce(
                    Sum(
                        F('lineas_servicio__cantidad') * F('lineas_servicio__precio_unitario') * (1 - F('lineas_servicio__descuento') / 100),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                ),
                sum_out=Coalesce(
                    Sum(
                        F('lineas_otro_servicio__precio_cliente') * F('lineas_otro_servicio__cantidad'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                ),
            )
            .annotate(
                total_general_anotado=F('sum_rep') + F('sum_serv') + F('sum_out')
            )
            .order_by('-fecha_emision', '-id')
        )
    except AttributeError:
        # Si el usuario no tiene empresa asignada, mostrar lista vacía
        documentos = Documento.objects.none()
    
    return render(request, 'taller/documentos/lista_documentos.html', {'documentos': documentos})

@login_required
def crear_documento(request):
    try:
        empresa = request.user.empresa
    except AttributeError:
        empresa = None

    if request.method == 'POST':
        form = DocumentoForm(request.POST, empresa=empresa)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.empresa = empresa
            documento.save()

            # Procesar repuestos y servicios desde el campo json_items
            json_items = request.POST.get('json_items')
            if json_items:
                try:
                    data = json.loads(json_items)
                    for item in data:
                        if item['tipo'] == 'repuesto':
                            LineaRepuesto.objects.create(
                                documento=documento,
                                codigo=item['partnumber'],
                                nombre=item['nombre'],
                                cantidad=item.get('cantidad', 1),
                                precio_unitario=item['precio'],
                            )
                        elif item['tipo'] == 'servicio':
                            LineaServicio.objects.create(
                                documento=documento,
                                nombre=item['nombre'],
                                precio_unitario=item['precio'],
                                cantidad=item.get('cantidad', 1)
                            )
                except json.JSONDecodeError:
                    pass
            return redirect('documentos:lista_documentos')
    else:
        form = DocumentoForm(empresa=empresa)

    # Cargar mecánicos activos del taller
    if empresa:
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)
    else:
        mecanicos = Tecnico.objects.none()

    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
        'mecanicos': mecanicos,
    })

@login_required
def editar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id, user=request.user)

    repuestos = LineaRepuesto.objects.filter(documento=documento)
    servicios = LineaServicio.objects.filter(documento=documento)
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
                    LineaRepuesto.objects.filter(documento=documento).delete()
                    LineaServicio.objects.filter(documento=documento).delete()
                    for item in data:
                        if item['tipo'] == 'repuesto':
                            LineaRepuesto.objects.create(
                                documento=documento,
                                codigo=item['partnumber'],
                                nombre=item['nombre'],
                                cantidad=item.get('cantidad', 1),
                                precio_unitario=item['precio'],
                            )
                        elif item['tipo'] == 'servicio':
                            LineaServicio.objects.create(
                                documento=documento,
                                nombre=item['nombre'],
                                precio_unitario=item['precio'],
                                cantidad=item.get('cantidad', 1)
                            )
                    # Recargar repuestos y servicios después de guardar
                    repuestos = LineaRepuesto.objects.filter(documento=documento)
                    servicios = LineaServicio.objects.filter(documento=documento)
                except json.JSONDecodeError:
                    pass
            return redirect('documentos:detalle_documento', documento_id=documento.pk)
    # Cargar mecánicos activos del taller
    mecanicos = Tecnico.objects.filter(activo=True)
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
