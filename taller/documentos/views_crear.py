from django.shortcuts import render, redirect
from django.db import transaction, models
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from .forms import DocumentoForm
from .formsets import RepuestoFormSet, ServicioFormSet, OtroServicioFormSet
from .models import Documento
from taller.models.sequence import DocumentSequence
from taller.models.tecnico import Tecnico
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio

def _prefix(tipo):
    """Mapea tipos de documento a prefijos de numeración"""
    return {'OT': 'OT', 'FAC': 'F', 'PRES': 'P'}.get(tipo, 'D')

def build_context(request, form=None, rep_fs=None, serv_fs=None, otro_fs=None):
    """
    Usar SIEMPRE este builder en GET y en POST inválido para evitar
    'context' incompleto que deje el template 'en blanco'.
    """
    try:
        empresa = request.user.empresa
        country = getattr(empresa, 'pais', 'CL') if empresa else 'CL'
    except AttributeError:
        country = 'CL'
    
    ctx = {
        'form': form or DocumentoForm(user=request.user),
        'rep_fs': rep_fs or RepuestoFormSet(prefix='rep'),
        'serv_fs': serv_fs or ServicioFormSet(prefix='serv'),
        'otro_fs': otro_fs or OtroServicioFormSet(prefix='otr'),
        'country': country,
        'tecnicos': Tecnico.objects.filter(empresa=empresa).order_by('nombre') if empresa else Tecnico.objects.none(),
        'clientes': Cliente.objects.filter(empresa=empresa).order_by('nombre') if empresa else Cliente.objects.none(),
        'vehiculos': Vehiculo.objects.filter(empresa=empresa).order_by('patente') if empresa else Vehiculo.objects.none(),
        'servicios': Servicio.objects.filter(empresa=empresa).order_by('nombre') if empresa else Servicio.objects.none(),
        'today': timezone.now().date(),
    }
    return ctx

@login_required
@transaction.atomic
def crear_documento(request):
    """Vista robusta para crear documentos con formsets - NUNCA deja pantalla en blanco"""
    
    print(f"[DOC][DEBUG] ========== INICIO CREAR DOCUMENTO ==========")
    print(f"[DOC][DEBUG] Usuario: {request.user.username}")
    print(f"[DOC][DEBUG] Método: {request.method}")
    
    try:
        # Obtener empresa del usuario (común para GET y POST)
        try:
            empresa = request.user.empresa
            print(f"[DOC][DEBUG] Empresa obtenida: {empresa.nombre_taller if empresa else 'None'}")
        except AttributeError:
            empresa = None
            print(f"[DOC][DEBUG] Usuario sin empresa")
        
        if request.method == 'POST':
            print(f"[DOC][DEBUG] Procesando POST...")
            print(f"[DOC][POST] Datos recibidos: {dict(request.POST)}")

            # Crear formularios con datos POST
            doc_form = DocumentoForm(request.POST, user=request.user)
            rep_fs = RepuestoFormSet(request.POST, prefix='rep')
            serv_fs = ServicioFormSet(request.POST, prefix='serv')
            otro_fs = OtroServicioFormSet(request.POST, prefix='otr')

            # Configurar empresa para formsets
            for form in rep_fs.forms:
                form.empresa = empresa
            for form in serv_fs.forms:
                form.empresa = empresa
            for form in otro_fs.forms:
                form.empresa = empresa

            # Validar todos los formularios
            forms_valid = all([
                doc_form.is_valid(), 
                rep_fs.is_valid(), 
                serv_fs.is_valid(), 
                otro_fs.is_valid()
            ])
            
            print(f"[DOC][DEBUG] Formularios válidos: {forms_valid}")
            
            if forms_valid:
                print(f"[DOC][DEBUG] Todos los formularios son válidos, guardando...")
                
                try:
                    # Crear documento
                    doc = doc_form.save(commit=False)
                    doc.empresa = empresa
                    
                    # Numeración automática
                    if not doc.numero:
                        n = DocumentSequence.next(empresa, doc.tipo)
                        doc.correlativo = n
                        pref = {'OT':'OT', 'FAC':'F', 'PRES':'P'}.get(doc.tipo,'D')
                        doc.numero = f"{pref}{n:03d}"
                        print(f"[DOC][DEBUG] Número generado: {doc.numero}")
                    
                    # Configurar campos automáticos
                    doc.country = getattr(empresa, 'pais', 'CL')
                    doc.moneda = getattr(getattr(empresa, 'configuracion', None), 'moneda', 'CLP') or 'CLP'
                    if not doc.estado:
                        doc.estado = 'EMITIDO'  # default seguro
                    
                    # Validar coherencia cliente-vehículo
                    cid = doc_form.cleaned_data.get('cliente').id
                    vid = doc_form.cleaned_data.get('vehiculo').id if doc_form.cleaned_data.get('vehiculo') else None
                    if vid and not Vehiculo.objects.filter(id=vid, cliente_id=cid, empresa=empresa).exists():
                        doc_form.add_error('vehiculo', 'El vehículo no pertenece al cliente seleccionado.')
                        raise ValidationError("El vehículo no pertenece al cliente seleccionado.")
                    
                    # Configurar IVA para Chile
                    if getattr(doc, 'country', 'CL') == 'CL':
                        doc.tax_rate_applied = 19
                    
                    # Guardar documento
                    doc.save()
                    print(f"[DOC][DEBUG] Documento guardado con ID: {doc.id}")

                    # Guardar líneas
                    rep_fs.instance = doc
                    rep_fs.save()
                    print(f"[DOC][DEBUG] Líneas de repuestos guardadas")
                    
                    serv_fs.instance = doc
                    serv_fs.save()
                    print(f"[DOC][DEBUG] Líneas de servicios guardadas")
                    
                    otro_fs.instance = doc
                    otro_fs.save()
                    print(f"[DOC][DEBUG] Líneas de otros servicios guardadas")

                    # Recalcular totales en servidor (autoridad)
                    try:
                        doc.recalcular_totales()
                        doc.save(update_fields=['neto_repuestos', 'neto_servicios', 'tax_amount', 'total'])
                        print(f"[DOC][DEBUG] Totales recalculados: {doc.total}")
                    except Exception as e:
                        print(f"[DOC][WARN] Error al recalcular totales: {e}")

                    messages.success(request, f'Documento {doc.numero} creado correctamente.')
                    url = reverse('taller:documentos:lista_documentos')
                    print(f"[DOC][DEBUG] Redirect exitoso a: {url}")
                    return redirect(url)
                    
                except Exception as e:
                    print(f"[DOC][ERROR] Error al guardar documento: {e}")
                    messages.error(request, f'Error al guardar documento: {str(e)}')
                    # Re-renderizar con contexto completo
                    ctx = build_context(request, doc_form, rep_fs, serv_fs, otro_fs)
                    return render(request, 'taller/cl/es/documentos/crear_documento.html', ctx, status=500)

            # Si hay errores, re-render con errores visibles (nunca en blanco)
            print(f"[DOC][DEBUG] Formularios inválidos, mostrando errores...")
            print(f"[DOC][ERROR] DOC ERR: {doc_form.errors.as_json() if doc_form.errors else 'N/A'}")
            print(f"[DOC][ERROR] REP ERR: {rep_fs.errors if rep_fs.errors else 'N/A'}")
            print(f"[DOC][ERROR] SERV ERR: {serv_fs.errors if serv_fs.errors else 'N/A'}")
            print(f"[DOC][ERROR] OTR ERR: {otro_fs.errors if otro_fs.errors else 'N/A'}")

            ctx = build_context(request, doc_form, rep_fs, serv_fs, otro_fs)
            return render(request, 'taller/cl/es/documentos/crear_documento.html', ctx, status=400)

        # GET - Mostrar formularios vacíos
        print(f"[DOC][DEBUG] Procesando GET...")
        ctx = build_context(request)
        return render(request, 'taller/cl/es/documentos/crear_documento.html', ctx)

    except Exception as e:
        # En desarrollo, deja rastro y evita respuesta vacía
        print(f"[DOC][ERROR 500] Error inesperado: {repr(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error inesperado al crear documento: {str(e)}')
        ctx = build_context(request)
        return render(request, 'taller/cl/es/documentos/crear_documento.html', ctx, status=500)

@login_required
def buscar_clientes_ajax(request):
    """Vista AJAX para buscar clientes por nombre o email"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        empresa = request.user.empresa
        
        if not query or len(query) < 2:
            return HttpResponse('[]', content_type='application/json')
        
        # Buscar clientes que coincidan con la consulta (nombre, apellido o teléfono)
        clientes = Cliente.objects.filter(
            empresa=empresa
        ).filter(
            models.Q(nombre__icontains=query) |
            models.Q(apellido__icontains=query) |
            models.Q(telefono__icontains=query)
        ).order_by('nombre', 'apellido')[:10]  # Limitar a 10 resultados
        
        # Formatear resultados para JSON
        resultados = []
        for cliente in clientes:
            # Crear nombre completo
            nombre_completo = f"{cliente.nombre} {cliente.apellido}".strip()
            
            # Crear texto de búsqueda con información relevante
            info_adicional = []
            if cliente.telefono:
                info_adicional.append(f"📞 {cliente.telefono}")
            if cliente.email:
                info_adicional.append(f"📧 {cliente.email}")
            
            info_text = " | ".join(info_adicional) if info_adicional else "Sin información adicional"
            
            resultados.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'apellido': cliente.apellido or '',
                'nombre_completo': nombre_completo,
                'email': cliente.email or '',
                'telefono': cliente.telefono or '',
                'text': f"{nombre_completo} ({info_text})"
            })
        
        import json
        return HttpResponse(json.dumps(resultados), content_type='application/json')
    
    return HttpResponse('[]', content_type='application/json')
