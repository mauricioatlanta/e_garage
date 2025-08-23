from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.documentos.forms import DocumentoForm
from decimal import Decimal
import json

# ===== VIEWS NUEVAS Y MEJORADAS =====

@login_required
def ver_documento_nuevo(request, documento_id):
    """Vista nueva y mejorada para ver documentos con repuestos y servicios"""
    print(f"[VER_NUEVO] ===== INICIANDO VER DOCUMENTO NUEVO =====")
    print(f"[VER_NUEVO] Usuario: {request.user.username}")
    print(f"[VER_NUEVO] Documento ID: {documento_id}")
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
        print(f"[VER_NUEVO] Empresa del usuario: {empresa.nombre_taller}")
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
        print(f"[VER_NUEVO] Empresa {'creada' if created else 'obtenida'}: {empresa.nombre_taller}")
    
    # Obtener documento con filtro de empresa
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    print(f"[VER_NUEVO] Documento encontrado: {documento.numero_documento} ({documento.tipo_documento})")
    
    # Obtener repuestos y servicios
    repuestos = LineaRepuesto.objects.filter(documento=documento).order_by('id')
    servicios = LineaServicio.objects.filter(documento=documento).order_by('id')
    
    print(f"[VER_NUEVO] Repuestos encontrados: {repuestos.count()}")
    for i, rep in enumerate(repuestos, 1):
        print(f"[VER_NUEVO]   {i}. {rep.nombre} - ${rep.precio_unitario} x {rep.cantidad} = ${rep.subtotal}")
    
    print(f"[VER_NUEVO] Servicios encontrados: {servicios.count()}")
    for i, serv in enumerate(servicios, 1):
        print(f"[VER_NUEVO]   {i}. {serv.nombre} - ${serv.precio_unitario}")
    
    # Calcular totales
    subtotal_repuestos = sum(rep.subtotal for rep in repuestos)
    subtotal_servicios = sum(serv.precio_unitario * serv.cantidad for serv in servicios)
    subtotal = subtotal_repuestos + subtotal_servicios
    iva = int(subtotal * Decimal('0.19'))
    total = subtotal + iva
    
    print(f"[VER_NUEVO] CÁLCULOS:")
    print(f"[VER_NUEVO]   Subtotal repuestos: ${subtotal_repuestos}")
    print(f"[VER_NUEVO]   Subtotal servicios: ${subtotal_servicios}")
    print(f"[VER_NUEVO]   Subtotal: ${subtotal}")
    print(f"[VER_NUEVO]   IVA: ${iva}")
    print(f"[VER_NUEVO]   TOTAL: ${total}")
    
    context = {
        'documento': documento,
        'repuestos': repuestos,
        'servicios': servicios,
        'subtotal_repuestos': subtotal_repuestos,
        'subtotal_servicios': subtotal_servicios,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
    }
    
    print(f"[VER_NUEVO] ===== RENDERIZANDO TEMPLATE NUEVO =====")
    return render(request, 'taller/documentos/ver_documento_nuevo.html', context)


@login_required
@login_required
def editar_documento_nuevo(request, documento_id):
    """Vista nueva y mejorada para editar documentos con repuestos y servicios"""
    print("🔥 VISTA EDITAR_DOCUMENTO_NUEVO EJECUTÁNDOSE 🔥")
    print(f"[EDITAR_NUEVO] ===== INICIANDO EDITAR DOCUMENTO NUEVO =====")
    print(f"[EDITAR_NUEVO] Usuario: {request.user.username}")
    print(f"[EDITAR_NUEVO] Documento ID: {documento_id}")
    print(f"[EDITAR_NUEVO] Método: {request.method}")
    print(f"[EDITAR_NUEVO] URL llamada: {request.path}")
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
        print(f"[EDITAR_NUEVO] Empresa del usuario: {empresa.nombre_taller}")
    except AttributeError as e:
        print(f"[EDITAR_NUEVO] Error obteniendo empresa: {e}")
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
        print(f"[EDITAR_NUEVO] Empresa {'creada' if created else 'obtenida'}: {empresa.nombre_taller}")
    
    # Obtener documento con filtro de empresa
    try:
        documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
        print(f"[EDITAR_NUEVO] Documento encontrado: {documento.numero_documento}")
    except Exception as e:
        print(f"[EDITAR_NUEVO] ERROR obteniendo documento: {e}")
        raise
    
    if request.method == 'POST':
        print(f"[EDITAR_NUEVO] ===== PROCESANDO POST =====")
        
        # Obtener datos del formulario
        form = DocumentoForm(request.POST, instance=documento, empresa=empresa)
        
        if form.is_valid():
            print(f"[EDITAR_NUEVO] Formulario válido")
            documento = form.save()
            
            # Procesar items JSON
            json_items = request.POST.get('json_items', '[]')
            print(f"[EDITAR_NUEVO] json_items recibido: {json_items}")
            
            try:
                items = json.loads(json_items)
                print(f"[EDITAR_NUEVO] Items parseados: {len(items)} items")
                
                # ELIMINAR TODOS LOS REPUESTOS Y SERVICIOS ANTERIORES
                repuestos_eliminados = documento.repuestos.count()
                servicios_eliminados = documento.servicios.count()

                documento.repuestos.all().delete()
                documento.servicios.all().delete()
                
                print(f"[EDITAR_NUEVO] Eliminados {repuestos_eliminados} repuestos y {servicios_eliminados} servicios anteriores")
                
                # CREAR NUEVOS REPUESTOS Y SERVICIOS
                repuestos_creados = 0
                servicios_creados = 0
                
                for i, item in enumerate(items):
                    print(f"[EDITAR_NUEVO] Procesando item {i+1}: {item}")
                    
                    # Validar datos básicos
                    nombre = item.get('nombre', '').strip()
                    precio = item.get('precio', 0)
                    
                    if isinstance(precio, str):
                        precio = int(precio.replace('$', '').replace(',', '') or 0)
                    else:
                        precio = int(precio or 0)
                    
                    if not nombre or precio <= 0:
                        print(f"[EDITAR_NUEVO] Item {i+1} rechazado - nombre: '{nombre}', precio: {precio}")
                        continue
                    
                    if item.get('tipo') == 'repuesto':
                        # Crear repuesto
                        repuesto = LineaRepuesto.objects.create(
                            documento=documento,
                            codigo=item.get('partnumber', '').strip() or f'EDIT-{i+1:03d}',
                            nombre=nombre,
                            cantidad=int(item.get('cantidad', 1)),
                            precio_unitario=precio
                        )
                        repuestos_creados += 1
                        print(f"[EDITAR_NUEVO] ✅ Repuesto creado: {repuesto.nombre} (${repuesto.precio} x {repuesto.cantidad})")
                        
                    elif item.get('tipo') == 'servicio':
                        # Crear servicio
                        servicio = LineaServicio.objects.create(
                            empresa=empresa,
                            documento=documento,
                            nombre=nombre,
                            precio_unitario=precio,
                            cantidad=1
                        )
                        servicios_creados += 1
                        print(f"[EDITAR_NUEVO] ✅ Servicio creado: {servicio.nombre} (${servicio.precio})")
                
                print(f"[EDITAR_NUEVO] RESUMEN: {repuestos_creados} repuestos, {servicios_creados} servicios creados")
                
            except json.JSONDecodeError as e:
                print(f"[EDITAR_NUEVO] ❌ Error JSON: {e}")
            except Exception as e:
                print(f"[EDITAR_NUEVO] ❌ Error procesando items: {e}")
                import traceback
                traceback.print_exc()
            
            # Redirigir al listado de documentos después de guardar
            from django.contrib import messages
            messages.success(request, f'Documento {documento.numero_documento} guardado exitosamente.')
            print(f"[EDITAR_NUEVO] ===== REDIRIGIENDO AL LISTADO DE DOCUMENTOS =====")
            return redirect('documentos:lista_documentos')
        else:
            print(f"[EDITAR_NUEVO] ❌ Formulario inválido: {form.errors}")
    
    else:
        # GET - mostrar formulario de edición
        form = DocumentoForm(instance=documento, empresa=empresa)
    
    # Obtener repuestos y servicios actuales
    repuestos = LineaRepuesto.objects.filter(documento=documento).order_by('id')
    servicios = LineaServicio.objects.filter(documento=documento).order_by('id')
    
    print(f"[EDITAR_NUEVO] ===== DEBUG DATOS =====")
    print(f"[EDITAR_NUEVO] Documento ID: {documento.id}")
    print(f"[EDITAR_NUEVO] Repuestos actuales: {repuestos.count()}")
    print(f"[EDITAR_NUEVO] Servicios actuales: {servicios.count()}")
    
    # Debug adicional - listar todos los repuestos y servicios
    for i, rep in enumerate(repuestos, 1):
        print(f"[EDITAR_NUEVO] Repuesto {i}: {rep.nombre} - ${rep.precio_unitario} x {rep.cantidad}")
    
    for i, serv in enumerate(servicios, 1):
        print(f"[EDITAR_NUEVO] Servicio {i}: {serv.nombre} - ${serv.precio_unitario}")
    
    # También verificar las tablas directas de la DB
    from django.db import connection
    cursor = connection.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM taller_lineaservicio WHERE documento_id = %s", [documento.id])
    count_lineaservicio = cursor.fetchone()[0]
    print(f"[EDITAR_NUEVO] Servicios en taller_lineaservicio: {count_lineaservicio}")
    
    cursor.execute("SELECT COUNT(*) FROM taller_lineaotroservicio WHERE documento_id = %s", [documento.id])
    count_otroservicio = cursor.fetchone()[0]
    print(f"[EDITAR_NUEVO] Otros servicios en taller_lineaotroservicio: {count_otroservicio}")
    
    print(f"[EDITAR_NUEVO] ===== FIN DEBUG =====")
    
    # Calcular totales
    subtotal_repuestos = sum(rep.subtotal for rep in repuestos)
    subtotal_servicios = sum(serv.precio_unitario * serv.cantidad for serv in servicios)
    subtotal = subtotal_repuestos + subtotal_servicios
    iva = int(subtotal * Decimal('0.19'))
    total = subtotal + iva
    
    context = {
        'form': form,
        'documento': documento,
        'repuestos': repuestos,
        'servicios': servicios,
        'subtotal_repuestos': subtotal_repuestos,
        'subtotal_servicios': subtotal_servicios,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
        'editando': True,
    }
    
    print(f"[EDITAR_NUEVO] ===== RENDERIZANDO TEMPLATE DE CREACIÓN (MODO EDICIÓN) =====")
    return render(request, 'taller/documentos/crear_documento.html', context)


@login_required
def test_documento_datos(request, documento_id):
    """Vista de test para verificar que los datos están en la base de datos"""
    print(f"[TEST] ===== TEST DE DATOS DEL DOCUMENTO =====")
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, _ = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    # Obtener documento
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    
    # Test directo en base de datos
    from taller.models.lineas_documento import LineaRepuesto as RepuestoDocumento, LineaServicio as ServicioLinea
    repuestos_count = RepuestoDocumento.objects.filter(documento=documento).count()
    servicios_count = ServicioLinea.objects.filter(documento=documento).count()
    
    repuestos = list(RepuestoDocumento.objects.filter(documento=documento).values())
    servicios = list(ServicioLinea.objects.filter(documento=documento).values())
    
    test_data = {
        'documento_id': documento.id,
        'numero_documento': documento.numero_documento,
        'empresa': documento.empresa.nombre_taller,
        'repuestos_count': repuestos_count,
        'servicios_count': servicios_count,
        'repuestos_data': repuestos,
        'servicios_data': servicios,
        'success': True
    }
    
    print(f"[TEST] Documento: {documento.numero_documento}")
    print(f"[TEST] Repuestos: {repuestos_count}")
    print(f"[TEST] Servicios: {servicios_count}")
    
    return JsonResponse(test_data)
