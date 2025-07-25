from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from taller.models.mecanico import Mecanico
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
# API para crear mecánico vía AJAX
@csrf_exempt
@require_POST
@login_required
def api_crear_mecanico(request):
    print(f"[DEBUG] API crear mecánico - Método: {request.method}")
    print(f"[DEBUG] POST data: {request.POST}")
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    nombre = request.POST.get('nombre', '').strip()
    print(f"[DEBUG] Nombre recibido: '{nombre}'")
    
    if not nombre:
        return JsonResponse({'error': 'Nombre requerido'}, status=400)
    
    try:
        from taller.models.mecanico import Mecanico
        # Crear mecánico asociado a la empresa del usuario
        mecanico, created = Mecanico.objects.get_or_create(
            nombre=nombre, 
            empresa=empresa,
            defaults={'activo': True}
        )
        
        response_data = {
            'id': mecanico.id, 
            'nombre': mecanico.nombre,
            'created': created
        }
        print(f"[DEBUG] Respuesta: {response_data}")
        
        return JsonResponse(response_data)
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
from django.views.decorators.http import require_GET

# --- AUTOCOMPLETE REPUESTO ---
@require_GET
@login_required
def autocomplete_repuesto(request):
    from taller.models.repuesto import Repuesto
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get('q', '')
    # Filtrar repuestos por empresa
    repuestos = Repuesto.objects.filter(part_number__icontains=q, empresa=empresa)[:10]
    results = [
        {
            'id': r.id,
            'partnumber': r.part_number,
            'nombre': r.nombre_repuesto,
            'precio': float(r.precio_venta)
        }
        for r in repuestos
    ]
    return JsonResponse({'results': results})

# --- AUTOCOMPLETE SERVICIO ---
@require_GET
@login_required
def autocomplete_servicio_nombre(request):
    from taller.servicios.models import Servicio
    
    # Los servicios son globales, pero requieren autenticación
    q = request.GET.get('q', '')
    servicios = Servicio.objects.filter(nombre__icontains=q)[:10]
    results = [
        {
            'id': s.id,
            'nombre': s.nombre
        }
        for s in servicios
    ]
    return JsonResponse({'results': results})
from django.http import JsonResponse
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio

@login_required
def obtener_vehiculos_por_cliente(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    cliente_id = request.GET.get('cliente_id') or request.GET.get('cliente')
    q = request.GET.get('q', '')
    
    if not cliente_id:
        return JsonResponse({'results': []})  # Devolver lista vacía en lugar de error
    
    try:
        cliente_id = int(cliente_id)
    except (ValueError, TypeError):
        return JsonResponse({'results': []})
    
    # Filtrar vehículos por cliente Y por empresa del usuario
    vehiculos = Vehiculo.objects.filter(cliente_id=cliente_id, empresa=empresa)
    
    # Si hay término de búsqueda, filtrar por patente
    if q:
        vehiculos = vehiculos.filter(patente__icontains=q)
    
    # Preparar datos para Select2
    results = []
    for vehiculo in vehiculos:
        marca = vehiculo.marca.nombre if vehiculo.marca else "Sin marca"
        modelo = vehiculo.modelo.nombre if vehiculo.modelo else "Sin modelo"
        results.append({
            'id': vehiculo.id,
            'text': f"{vehiculo.patente} - {marca} {modelo}",
            'patente': vehiculo.patente,
            'marca': marca,
            'modelo': modelo
        })
    
    return JsonResponse({'results': results})

@login_required
def autocomplete_cliente(request):
    """Vista de autocompletado para clientes específica para documentos"""
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get('q', '')
    
    # Filtrar clientes por empresa del usuario
    clientes = Cliente.objects.filter(empresa=empresa)
    
    # Si hay término de búsqueda, filtrar por nombre, email o teléfono
    if q:
        from django.db.models import Q
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )
    
    # Preparar datos para Select2
    results = []
    for cliente in clientes[:20]:  # Limitar a 20 resultados
        apellido = cliente.apellido or ""
        nombre_completo = f"{cliente.nombre} {apellido}".strip()
        results.append({
            'id': cliente.pk,
            'text': nombre_completo,
            'nombre': cliente.nombre,
            'apellido': apellido,
            'email': cliente.email or '',
            'telefono': cliente.telefono or ''
        })
    
    return JsonResponse({'results': results})

@login_required
def autocomplete_servicio(request):
    # Los servicios son globales, pero requieren autenticación
    q = request.GET.get('q', '')
    servicios = Servicio.objects.filter(nombre__icontains=q)[:20]
    results = [
        {
            'id': s.id,
            'text': s.nombre,
            'precio': getattr(s, 'precio', None)  # Si el modelo tiene precio
        }
        for s in servicios
    ]
    return JsonResponse({'results': results})

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import json
from weasyprint import HTML
from django.conf import settings
from django.views.decorators.http import require_GET
from taller.documentos.models import  DetalleDocumento
from taller.models.documento import Documento
from taller.documentos.forms import DocumentoForm
from taller.forms.formsets import DetalleDocumentoFormSet
import os

 

from django.contrib.auth.decorators import login_required

@login_required
def crear_documento(request):
    print(f"[DEBUG CREAR] ========== VERSIÓN CORREGIDA - INICIO CREAR DOCUMENTO ==========")
    print(f"[DEBUG CREAR] Usuario: {request.user.username}")
    print(f"[DEBUG CREAR] Método: {request.method}")
    
    # Obtener empresa del usuario (común para GET y POST)
    try:
        empresa = request.user.empresa  # related_name desde el modelo Empresa
        print(f"[DEBUG CREAR] Empresa obtenida: {empresa.nombre_taller}")
    except AttributeError:
        # Si no existe la relación, crear/obtener empresa para el usuario
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
        print(f"[DEBUG CREAR] Empresa {'creada' if created else 'encontrada'}: {empresa.nombre_taller}")
    
    if request.method == 'POST':
        print(f"[DEBUG CREAR] ===== PROCESANDO POST =====")
        post_data = request.POST.copy()
        print(f"[DEBUG CREAR] Datos POST recibidos: {list(post_data.keys())}")
        print(f"[DEBUG CREAR] json_items: {post_data.get('json_items')}")
        
        # Manejar mecánico (si es texto, crear mecánico nuevo)
        mecanico_id = post_data.get('mecanico')
        if mecanico_id and not mecanico_id.isdigit():
            from taller.models.mecanico import Mecanico
            mecanico_obj, _ = Mecanico.objects.get_or_create(nombre=mecanico_id, empresa=empresa)
            post_data['mecanico'] = mecanico_obj.pk
            print(f"[DEBUG CREAR] Mecánico creado/encontrado: {mecanico_obj.nombre} (ID: {mecanico_obj.pk})")
            
        form = DocumentoForm(post_data, empresa=empresa)
        if form.is_valid():
            print(f"[DEBUG CREAR] Formulario válido")
            documento = form.save(commit=False)
            documento.empresa = empresa
            
            # Generar número de documento si no existe
            if not documento.numero_documento:
                tipo = documento.tipo_documento.lower().replace(" ", "_")
                count = Documento.objects.filter(
                    tipo_documento=documento.tipo_documento,
                    empresa=empresa
                ).count() + 1
                documento.numero_documento = f"{tipo[:3].upper()}-{count:05d}"
                print(f"[DEBUG CREAR] Número generado: {documento.numero_documento}")
                
            documento.save()
            form.save_m2m()
            
            # Procesar ítems desde JSON (repuestos y servicios)
            json_items = post_data.get('json_items')
            print(f"[DEBUG CREAR] json_items recibido: {json_items}")
            if json_items is not None and json_items.strip() not in ['', '[]', 'null']:
                try:
                    items = json.loads(json_items)
                    print(f"[DEBUG CREAR] Items parseados: {len(items)} items")
                    from taller.models.documento import RepuestoDocumento, ServicioDocumento
                    
                    for item in items:
                        print(f"[DEBUG CREAR] Procesando item: {item}")
                        tipo = item.get('tipo')
                        nombre = item.get('nombre', '').strip()
                        precio = float(item.get('precio', 0))
                        
                        if tipo == 'repuesto' and nombre and precio > 0:
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item.get('partnumber', '').strip(),
                                nombre=nombre,
                                cantidad=int(item.get('cantidad', 1)),
                                precio=precio
                            )
                            print(f"[DEBUG CREAR] ✅ Repuesto guardado: {nombre} (${precio})")
                            
                        elif tipo == 'servicio' and nombre and precio > 0:
                            ServicioDocumento.objects.create(
                                empresa=empresa,
                                documento=documento,
                                nombre=nombre,
                                precio=precio
                            )
                            print(f"[DEBUG CREAR] ✅ Servicio guardado: {nombre} (${precio})")
                            
                        elif tipo == 'otro_servicio' and nombre and precio > 0:
                            # Buscar o crear el servicio en el catálogo
                            from taller.servicios.models import Servicio
                            servicio_obj, created = Servicio.objects.get_or_create(nombre=nombre)
                            if created:
                                print(f"[DEBUG CREAR] ➕ Nuevo servicio creado en catálogo: {nombre}")
                            
                            from taller.models.documento import OtroServicioDocumento
                            OtroServicioDocumento.objects.create(
                                documento=documento,
                                servicio=servicio_obj,
                                nombre_servicio=nombre,
                                empresa_externa=item.get('empresa', '').strip(),
                                costo_interno=int(item.get('costo', 0)),
                                precio_cliente=int(precio),
                                observaciones=item.get('observaciones', '').strip()
                            )
                            print(f"[DEBUG CREAR] ✅ Otro servicio guardado: {nombre} - {item.get('empresa', '')} (${precio})")
                        else:
                            print(f"[DEBUG CREAR] Item ignorado por datos incompletos o inválidos: {item}")
                            
                except Exception as e:
                    print(f"❌ Error procesando json_items: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[DEBUG CREAR] json_items es None o vacío - no se recibieron items")
                
            return redirect('documentos:editar_documento', documento_id=documento.id)
        else:
            print(f"[DEBUG CREAR] Formulario inválido: {form.errors}")
            print(f"[DEBUG CREAR] ❌ DOCUMENTO NO CREADO - ERRORES EN FORMULARIO")
            
            # Agregar mensajes de error para mostrar al usuario
            from django.contrib import messages
            messages.error(request, f"Error al crear documento: {form.errors}")
            
            return redirect('documentos:lista_documentos')
    else:
        # GET: Mostrar formulario vacío
        from datetime import date
        hoy = date.today().strftime('%Y-%m-%d')
        form = DocumentoForm(initial={'fecha': hoy}, empresa=empresa)

    # Cargar mecánicos activos del taller
    from taller.models.mecanico import Mecanico
    mecanicos = Mecanico.objects.filter(empresa=empresa, activo=True)

    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
        'mecanicos': mecanicos,
    })

@login_required
def ver_documento(request, documento_id):
    print(f"[DEBUG VER] Solicitando documento ID: {documento_id}")
    print(f"[DEBUG VER] Usuario: {request.user.username}")
    
    # Verificar que el documento pertenece a la empresa del usuario
    try:
        empresa = request.user.empresa
        print(f"[DEBUG VER] Empresa del usuario: {empresa.nombre_taller}")
        documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
        print(f"[DEBUG VER] Documento encontrado: {documento.numero_documento}")
    except AttributeError:
        print(f"[DEBUG VER] Usuario sin empresa asociada")
        # Si no tiene empresa asociada, no puede ver ningún documento
        from django.http import Http404
        raise Http404("Documento no encontrado")
    
    # Usar importación directa para evitar problemas de related_name
    from taller.models.documento import RepuestoDocumento, ServicioDocumento, OtroServicioDocumento
    
    repuestos = RepuestoDocumento.objects.filter(documento=documento)
    servicios = ServicioDocumento.objects.filter(documento=documento)
    otros_servicios = OtroServicioDocumento.objects.filter(documento=documento)
    
    print(f"[DEBUG VER] Repuestos encontrados: {repuestos.count()}")
    for rep in repuestos:
        print(f"[DEBUG VER]   - {rep.nombre}: ${rep.precio} x {rep.cantidad}")
    
    print(f"[DEBUG VER] Servicios encontrados: {servicios.count()}")
    for serv in servicios:
        print(f"[DEBUG VER]   - {serv.nombre}: ${serv.precio}")
    
    print(f"[DEBUG VER] Otros servicios encontrados: {otros_servicios.count()}")
    for otro in otros_servicios:
        print(f"[DEBUG VER]   - {otro.nombre_servicio} ({otro.empresa_externa}): ${otro.precio_cliente}")
    
    subtotal_repuestos = sum(r.total for r in repuestos)
    subtotal_servicios = sum(s.precio for s in servicios)
    subtotal_otros_servicios = sum(o.precio_cliente for o in otros_servicios)
    subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
    iva = subtotal * 0.19
    total = subtotal + iva
    
    print(f"[DEBUG VER] Totales - Repuestos: ${subtotal_repuestos}, Servicios: ${subtotal_servicios}, Otros Servicios: ${subtotal_otros_servicios}, Total: ${total}")

    return render(request, 'taller/documentos/ver_documento.html', {
        'documento': documento,
        'repuestos': repuestos,
        'servicios': servicios,
        'otros_servicios': otros_servicios,
        'subtotal_repuestos': subtotal_repuestos,
        'subtotal_servicios': subtotal_servicios,
        'subtotal_otros_servicios': subtotal_otros_servicios,
        'subtotal': subtotal,
        'iva': iva,
        'total': total
    })



@login_required
def lista_documentos(request):
    # Filtrar documentos por empresa del usuario
    try:
        empresa = request.user.empresa
        documentos = Documento.objects.filter(empresa=empresa)
    except AttributeError:
        # Si no tiene empresa asociada, no mostrar documentos
        documentos = Documento.objects.none()
    
    return render(request, 'taller/documentos/lista_documentos.html', {'documentos': documentos})


@login_required
def editar_documento(request, documento_id):
    # Verificar que el documento pertenece a la empresa del usuario
    try:
        empresa = request.user.empresa
        documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    except AttributeError:
        # Si no tiene empresa asociada, no puede editar ningún documento
        from django.http import Http404
        raise Http404("Documento no encontrado")
    
    if request.method == 'POST':
        print(f"[DEBUG EDICIÓN] POST data recibido: {list(request.POST.keys())}")
        print(f"[DEBUG EDICIÓN] json_items: {request.POST.get('json_items')}")
        
        # Procesar mecánico nuevo si es necesario (igual que en crear_documento)
        post_data = request.POST.copy()
        mecanico_nombre = post_data.get('mecanico')
        if mecanico_nombre and not mecanico_nombre.isdigit():
            # Si el valor no es un ID, es un nombre nuevo o existente
            from taller.models.mecanico import Mecanico
            mecanico_obj, _ = Mecanico.objects.get_or_create(nombre=mecanico_nombre, empresa=empresa)
            post_data['mecanico'] = mecanico_obj.pk
            print(f"[DEBUG EDICIÓN] Mecánico creado/encontrado: {mecanico_obj.nombre} (ID: {mecanico_obj.pk})")
        elif mecanico_nombre and mecanico_nombre.isdigit():
            # Si es un ID, mantenerlo como está pero validar que pertenece a la empresa
            try:
                from taller.models.mecanico import Mecanico
                mecanico_obj = Mecanico.objects.get(pk=int(mecanico_nombre), empresa=empresa)  # 🔒 FILTRO EMPRESA
                post_data['mecanico'] = mecanico_obj.pk
            except Mecanico.DoesNotExist:
                pass
        
        form = DocumentoForm(post_data, instance=documento, empresa=empresa)
        if form.is_valid():
            print(f"[DEBUG EDICIÓN] Formulario válido")
    if request.method == 'POST':
        print(f"[DEBUG EDICIÓN] POST data recibido: {list(request.POST.keys())}")
        print(f"[DEBUG EDICIÓN] json_items: {request.POST.get('json_items')}")
        post_data = request.POST.copy()
        mecanico_nombre = post_data.get('mecanico')
        if mecanico_nombre and not mecanico_nombre.isdigit():
            from taller.models.mecanico import Mecanico
            mecanico_obj, _ = Mecanico.objects.get_or_create(nombre=mecanico_nombre, empresa=empresa)
            post_data['mecanico'] = mecanico_obj.pk
            print(f"[DEBUG EDICIÓN] Mecánico creado/encontrado: {mecanico_obj.nombre} (ID: {mecanico_obj.pk})")
        elif mecanico_nombre and mecanico_nombre.isdigit():
            try:
                from taller.models.mecanico import Mecanico
                mecanico_obj = Mecanico.objects.get(pk=int(mecanico_nombre), empresa=empresa)  # 🔒 FILTRO EMPRESA
                post_data['mecanico'] = mecanico_obj.pk
            except Mecanico.DoesNotExist:
                pass
        form = DocumentoForm(post_data, instance=documento, empresa=empresa)
        if form.is_valid():
            print(f"[DEBUG EDICIÓN] Formulario válido")
            documento = form.save()
            json_items = request.POST.get('json_items')
            print(f"[DEBUG EDICIÓN] json_items recibido: {json_items}")
            if json_items is not None and json_items.strip() not in ['', '[]', 'null']:
                try:
                    items = json.loads(json_items)
                    print(f"[DEBUG EDICIÓN] Items parseados: {len(items)} items")
                    from taller.models.documento import RepuestoDocumento, ServicioDocumento, OtroServicioDocumento
                    repuestos_anteriores = documento.repuestos.count()
                    servicios_anteriores = documento.servicios.count()
                    otros_servicios_anteriores = documento.otros_servicios.count()
                    documento.repuestos.all().delete()
                    documento.servicios.all().delete()
                    documento.otros_servicios.all().delete()
                    print(f"[DEBUG EDICIÓN] Eliminados {repuestos_anteriores} repuestos, {servicios_anteriores} servicios y {otros_servicios_anteriores} otros servicios anteriores")
                    for item in items:
                        print(f"[DEBUG EDICIÓN] Procesando item: {item}")
                        tipo = item.get('tipo')
                        nombre = item.get('nombre', '').strip()
                        precio = float(item.get('precio', 0))
                        if tipo == 'repuesto' and nombre and precio > 0:
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item.get('partnumber', '').strip(),
                                nombre=nombre,
                                cantidad=int(item.get('cantidad', 1)),
                                precio=precio
                            )
                            print(f"[DEBUG EDICIÓN] ✅ Repuesto guardado: {nombre} (${precio})")
                        elif tipo == 'servicio' and nombre and precio > 0:
                            ServicioDocumento.objects.create(
                                empresa=empresa,
                                documento=documento,
                                nombre=nombre,
                                precio=precio
                            )
                            print(f"[DEBUG EDICIÓN] ✅ Servicio guardado: {nombre} (${precio})")
                        elif tipo == 'otro_servicio' and nombre and precio > 0:
                            # Buscar o crear el servicio en el catálogo
                            from taller.servicios.models import Servicio
                            servicio_obj, created = Servicio.objects.get_or_create(nombre=nombre)
                            if created:
                                print(f"[DEBUG EDICIÓN] ➕ Nuevo servicio creado en catálogo: {nombre}")
                            
                            OtroServicioDocumento.objects.create(
                                documento=documento,
                                servicio=servicio_obj,
                                nombre_servicio=nombre,
                                empresa_externa=item.get('empresa', '').strip(),
                                costo_interno=int(item.get('costo', 0)),
                                precio_cliente=int(precio),
                                observaciones=item.get('observaciones', '').strip()
                            )
                            print(f"[DEBUG EDICIÓN] ✅ Otro servicio guardado: {nombre} - {item.get('empresa', '')} (${precio})")
                        else:
                            print(f"[DEBUG EDICIÓN] Item ignorado por datos incompletos o inválidos: {item}")
                except Exception as e:
                    print(f"❌ Error procesando json_items al editar: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[DEBUG EDICIÓN] json_items es None o vacío - no se recibieron items")
            return redirect('documentos:editar_documento', documento_id=documento.id)
        else:
            print(f"[DEBUG EDICIÓN] Formulario inválido: {form.errors}")
    else:
        # GET request - crear formulario para edición
        form = DocumentoForm(instance=documento, empresa=empresa)
    
    # Definir servicios y repuestos antes de los prints de debug
    from taller.models.documento import RepuestoDocumento, ServicioDocumento, OtroServicioDocumento
    servicios = ServicioDocumento.objects.filter(documento=documento)
    repuestos = RepuestoDocumento.objects.filter(documento=documento)
    otros_servicios = OtroServicioDocumento.objects.filter(documento=documento)
    print(f"[DEBUG EDITAR] Servicios encontrados: {servicios.count()}")
    for serv in servicios:
        print(f"[DEBUG EDITAR]   - {serv.nombre}: ${serv.precio}")
    print(f"[DEBUG EDITAR] Otros servicios encontrados: {otros_servicios.count()}")
    for otro in otros_servicios:
        print(f"[DEBUG EDITAR]   - {otro.nombre_servicio} ({otro.empresa_externa}): ${otro.precio_cliente}")

    # Calcular subtotales
    subtotal_repuestos = sum(r.total for r in repuestos)
    subtotal_servicios = sum(s.precio for s in servicios)
    subtotal_otros_servicios = sum(o.precio_cliente for o in otros_servicios)
    subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
    iva = subtotal * 0.19
    total = subtotal + iva

    # Cargar mecánicos activos del taller
    from taller.models.mecanico import Mecanico
    mecanicos = Mecanico.objects.filter(empresa=empresa, activo=True)

    return render(request, 'taller/documentos/editar_documento_nuevo.html', {
        'form': form,
        'documento': documento,  # Pasar documento al template
        'servicios': servicios,
        'repuestos': repuestos,
        'otros_servicios': otros_servicios,
        'subtotal_repuestos': subtotal_repuestos,
        'subtotal_servicios': subtotal_servicios,
        'subtotal_otros_servicios': subtotal_otros_servicios,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
        'editando': True,  # Indicar que estamos editando
        'mecanicos': mecanicos,
    })


@login_required
def eliminar_documento(request, documento_id):
    # Verificar que el documento pertenece a la empresa del usuario
    try:
        empresa = request.user.empresa
        documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    except AttributeError:
        # Si no tiene empresa asociada, no puede eliminar ningún documento
        from django.http import Http404
        raise Http404("Documento no encontrado")
    
    # Solo permitir eliminación si el usuario tiene permisos
    if request.method == 'GET':
        try:
            numero_doc = documento.numero_documento
            tipo_doc = documento.tipo_documento
            documento.delete()
            from django.contrib import messages
            messages.success(request, f'Documento {tipo_doc} #{numero_doc} eliminado correctamente.')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error al eliminar el documento: {str(e)}')
    
    return redirect('documentos:lista_documentos')


@csrf_exempt
def editar_detalle_documento(request):
    data = json.loads(request.body)
    detalle = get_object_or_404(DetalleDocumento, id=data['id'])
    campo = data['campo']
    valor = float(data['valor'])

    if campo in ['cantidad', 'precio_venta']:
        setattr(detalle, campo, valor)
        detalle.save()
        subtotal = detalle.cantidad * detalle.precio_venta
        return JsonResponse({'valor': valor, 'subtotal': int(subtotal)})

    return JsonResponse({'error': 'Campo inválido'}, status=400)


def total_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    return JsonResponse({
        'total_repuestos': documento.total_repuestos(),
        'total_servicios': documento.total_servicios(),
        'iva': documento.iva(),
        'total_general': documento.total_general()
    })


@require_GET
@login_required
def numero_documento_auto(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    tipo = request.GET.get("tipo")
    if not tipo:
        return JsonResponse({"error": "Tipo no proporcionado"}, status=400)

    # Filtrar por empresa para generar número correcto
    count = Documento.objects.filter(tipo_documento=tipo, empresa=empresa).count() + 1  # 🔒 FILTRO EMPRESA
    tipo_key = tipo.lower().replace(" ", "_")[:3].upper()
    numero = f"{tipo_key}-{count:05d}"

    return JsonResponse({"numero": numero})



def exportar_documento_pdf(request, documento_id):
    doc = get_object_or_404(Documento, id=documento_id)
    template = get_template('taller/pdf/documento.html')
    html = template.render({'documento': doc})

    response = HttpResponse(content_type='application/pdf')
    pisa.CreatePDF(html, dest=response)
    return response

def enviar_por_whatsapp(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Renderizar PDF y guardar archivo
    template = get_template("documentos/documento_pdf.html")
    html_string = template.render({"documento": documento})
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # Guardar el archivo en /media/pdfs/
    nombre_archivo = f"documento_{documento.numero}.pdf"
    path_archivo = os.path.join(settings.MEDIA_ROOT, "pdfs", nombre_archivo)

    os.makedirs(os.path.dirname(path_archivo), exist_ok=True)
    with open(path_archivo, "wb") as f:
        f.write(pdf)

    # Preparar mensaje de WhatsApp
    telefono = documento.cliente.telefono.replace("+", "").replace(" ", "")
    url_pdf = request.build_absolute_uri(f"{settings.MEDIA_URL}pdfs/{nombre_archivo}")
    mensaje = f"Hola {documento.cliente.nombre}, puedes ver tu {documento.tipo} aquí: {url_pdf}"
    enlace_whatsapp = f"https://wa.me/56{telefono}?text={mensaje.replace(' ', '%20')}"

    return redirect(enlace_whatsapp)
