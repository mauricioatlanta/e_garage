# views_documento_mejorado.py - Con auditoría y control de permisos
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.mecanico import Mecanico
from taller.models.perfilusuario import PerfilUsuario
from taller.models.auditoria import LogAuditoria
from taller.forms import DocumentoForm
import json


def log_auditoria_documento(usuario, empresa, accion, documento=None, descripcion="", request=None):
    """Helper para crear logs de auditoría específicos de documentos"""
    LogAuditoria.log_accion(
        usuario=usuario,
        empresa=empresa,
        accion=accion,
        modelo='DOCUMENTO',
        objeto_id=documento.pk if documento else None,
        descripcion=descripcion,
        request=request
    )


@login_required
def lista_documentos(request):
    """Lista documentos con control de empresa y auditoría"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Usuario sin perfil de empresa configurado")
        return redirect('dashboard')
    
    # Control de acceso por empresa
    if perfil.es_superadmin:
        documentos = Documento.objects.all()
        descripcion = "Acceso a lista completa de documentos (superadmin)"
    else:
        documentos = Documento.objects.filter(empresa=perfil.empresa)
        descripcion = f"Acceso a lista de documentos de {perfil.empresa.nombre_taller}"
    
    # Log de auditoría
    log_auditoria_documento(
        usuario=request.user,
        empresa=perfil.empresa,
        accion='VIEW',
        descripcion=descripcion,
        request=request
    )
    
    return render(request, 'taller/documentos/lista_documentos.html', {
        'documentos': documentos,
        'total_documentos': documentos.count()
    })


@login_required
def crear_documento(request):
    """Crear documento con auditoría completa"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Usuario sin perfil de empresa configurado")
        return redirect('dashboard')
    
    # Verificar permisos de rol
    if perfil.rol not in ['admin', 'vendedor'] and not perfil.es_superadmin:
        log_auditoria_documento(
            usuario=request.user,
            empresa=perfil.empresa,
            accion='CREATE',
            descripcion=f"Intento de creación de documento sin permisos (rol: {perfil.rol})",
            request=request
        )
        raise PermissionDenied("Su rol no tiene permisos para crear documentos")

    if request.method == 'POST':
        form = DocumentoForm(request.POST)
        if form.is_valid():
            # Datos antes de crear
            datos_antes = None
            
            # Crear documento
            documento = form.save(commit=False)
            documento.empresa = perfil.empresa
            documento.save()
            
            # Datos después de crear
            datos_despues = {
                'id': documento.pk,
                'numero_documento': documento.numero_documento,
                'tipo_documento': documento.tipo_documento,
                'fecha': str(documento.fecha),
                'cliente_id': documento.cliente.pk if documento.cliente else None,
                'vehiculo_id': documento.vehiculo.pk if documento.vehiculo else None,
            }
            
            # Procesar repuestos y servicios
            repuestos_creados = []
            servicios_creados = []
            
            json_items = request.POST.get('json_items')
            if json_items:
                try:
                    data = json.loads(json_items)
                    for item in data:
                        if item['tipo'] == 'repuesto':
                            repuesto = RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item['partnumber'],
                                nombre=item['nombre'],
                                cantidad=item['cantidad'],
                                precio=item['precio'],
                            )
                            repuestos_creados.append({
                                'codigo': repuesto.codigo,
                                'nombre': repuesto.nombre,
                                'cantidad': repuesto.cantidad,
                                'precio': repuesto.precio
                            })
                            
                        elif item['tipo'] == 'servicio':
                            servicio = ServicioDocumento.objects.create(
                                empresa=perfil.empresa,
                                documento=documento,
                                nombre=item['nombre'],
                                precio=item['precio'],
                            )
                            servicios_creados.append({
                                'nombre': servicio.nombre,
                                'precio': servicio.precio
                            })
                    
                    # Agregar items a datos después
                    datos_despues['repuestos'] = repuestos_creados
                    datos_despues['servicios'] = servicios_creados
                    
                except json.JSONDecodeError as e:
                    messages.error(request, f"Error procesando items del documento: {e}")
                    
                    # Log del error
                    log_auditoria_documento(
                        usuario=request.user,
                        empresa=perfil.empresa,
                        accion='CREATE',
                        documento=documento,
                        descripcion=f"Error al procesar items JSON: {e}",
                        request=request
                    )
            
            # Log de auditoría exitoso
            total_repuestos = len(repuestos_creados)
            total_servicios = len(servicios_creados)
            descripcion = f"Documento creado: {documento.numero_documento} con {total_repuestos} repuestos y {total_servicios} servicios"
            
            log_auditoria_documento(
                usuario=request.user,
                empresa=perfil.empresa,
                accion='CREATE',
                documento=documento,
                descripcion=descripcion,
                request=request
            )
            
            messages.success(request, f"Documento {documento.numero_documento} creado exitosamente")
            return redirect('documentos:lista_documentos')
        else:
            # Log de errores de validación
            errores = "; ".join([f"{campo}: {error}" for campo, error in form.errors.items()])
            log_auditoria_documento(
                usuario=request.user,
                empresa=perfil.empresa,
                accion='CREATE',
                descripcion=f"Intento fallido de crear documento. Errores: {errores}",
                request=request
            )
            messages.error(request, "Error en los datos del formulario")
    else:
        form = DocumentoForm()
        
        # Log de acceso a formulario
        log_auditoria_documento(
            usuario=request.user,
            empresa=perfil.empresa,
            accion='VIEW',
            descripcion="Acceso a formulario de crear documento",
            request=request
        )

    # Cargar mecánicos activos del taller
    mecanicos = Mecanico.objects.filter(empresa=perfil.empresa, activo=True)

    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
        'mecanicos': mecanicos,
    })


@login_required
def editar_documento(request, documento_id):
    """Editar documento con auditoría de cambios"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Usuario sin perfil de empresa configurado")
        return redirect('dashboard')

    # Obtener documento con control de empresa
    if perfil.es_superadmin:
        documento = get_object_or_404(Documento, id=documento_id)
    else:
        documento = get_object_or_404(Documento, id=documento_id, empresa=perfil.empresa)

    # Datos antes de editar
    datos_antes = {
        'numero_documento': documento.numero_documento,
        'tipo_documento': documento.tipo_documento,
        'fecha': str(documento.fecha),
        'observaciones': documento.observaciones,
        'repuestos': list(RepuestoDocumento.objects.filter(documento=documento).values()),
        'servicios': list(ServicioDocumento.objects.filter(documento=documento).values())
    }

    repuestos = RepuestoDocumento.objects.filter(documento=documento)
    servicios = ServicioDocumento.objects.filter(documento=documento)
    
    if request.method == 'POST':
        form = DocumentoForm(request.POST, instance=documento)
        if form.is_valid():
            documento_actualizado = form.save()

            # Procesar repuestos y servicios actualizados
            json_items = request.POST.get('json_items')
            if json_items:
                try:
                    data = json.loads(json_items)

                    # Eliminar ítems anteriores
                    RepuestoDocumento.objects.filter(documento=documento).delete()
                    ServicioDocumento.objects.filter(documento=documento).delete()

                    # Crear nuevos ítems
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
                    
                except json.JSONDecodeError as e:
                    messages.error(request, f"Error procesando items: {e}")

            # Datos después de editar
            datos_despues = {
                'numero_documento': documento.numero_documento,
                'tipo_documento': documento.tipo_documento,
                'fecha': str(documento.fecha),
                'observaciones': documento.observaciones,
                'repuestos': list(RepuestoDocumento.objects.filter(documento=documento).values()),
                'servicios': list(ServicioDocumento.objects.filter(documento=documento).values())
            }

            # Log de auditoría con cambios
            descripcion = f"Documento editado: {documento.numero_documento}"
            log_auditoria_documento(
                usuario=request.user,
                empresa=perfil.empresa,
                accion='UPDATE',
                documento=documento,
                descripcion=descripcion,
                request=request
            )

            messages.success(request, f"Documento {documento.numero_documento} actualizado exitosamente")
            return redirect('documentos:detalle_documento', documento_id=documento.pk)
    else:
        form = DocumentoForm(instance=documento)
        
        # Log de acceso a edición
        log_auditoria_documento(
            usuario=request.user,
            empresa=perfil.empresa,
            accion='VIEW',
            documento=documento,
            descripcion=f"Acceso a editar documento: {documento.numero_documento}",
            request=request
        )

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
    """Ver detalle de documento con auditoría"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Usuario sin perfil de empresa configurado")
        return redirect('dashboard')

    # Control de acceso por empresa
    if perfil.es_superadmin:
        documento = get_object_or_404(Documento, id=documento_id)
    else:
        documento = get_object_or_404(Documento, id=documento_id, empresa=perfil.empresa)
    
    # Log de auditoría
    log_auditoria_documento(
        usuario=request.user,
        empresa=perfil.empresa,
        accion='VIEW',
        documento=documento,
        descripcion=f"Visualización de documento: {documento.numero_documento}",
        request=request
    )
    
    return render(request, 'taller/documentos/detalle_documento.html', {
        'documento': documento
    })


@login_required 
def eliminar_documento(request, documento_id):
    """Eliminar documento con auditoría"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Usuario sin perfil de empresa configurado")
        return redirect('dashboard')

    # Verificar permisos de rol
    if perfil.rol not in ['admin'] and not perfil.es_superadmin:
        log_auditoria_documento(
            usuario=request.user,
            empresa=perfil.empresa,
            accion='DELETE',
            descripcion=f"Intento de eliminación sin permisos (rol: {perfil.rol})",
            request=request
        )
        raise PermissionDenied("Su rol no tiene permisos para eliminar documentos")

    # Control de acceso por empresa
    if perfil.es_superadmin:
        documento = get_object_or_404(Documento, id=documento_id)
    else:
        documento = get_object_or_404(Documento, id=documento_id, empresa=perfil.empresa)

    if request.method == 'POST':
        # Datos antes de eliminar
        datos_antes = {
            'numero_documento': documento.numero_documento,
            'tipo_documento': documento.tipo_documento,
            'fecha': str(documento.fecha),
            'cliente': str(documento.cliente) if documento.cliente else None,
            'repuestos_count': RepuestoDocumento.objects.filter(documento=documento).count(),
            'servicios_count': ServicioDocumento.objects.filter(documento=documento).count()
        }

        numero_doc = documento.numero_documento
        documento.delete()

        # Log de auditoría
        log_auditoria_documento(
            usuario=request.user,
            empresa=perfil.empresa,
            accion='DELETE',
            descripcion=f"Documento eliminado: {numero_doc}",
            request=request
        )

        messages.success(request, f"Documento {numero_doc} eliminado exitosamente")
        return redirect('documentos:lista_documentos')

    return render(request, 'taller/documentos/confirmar_eliminar.html', {
        'documento': documento
    })
