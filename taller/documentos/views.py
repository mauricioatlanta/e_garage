from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from taller.models.mecanico import Mecanico
# API para crear mecánico vía AJAX
@csrf_exempt
@require_POST
def api_crear_mecanico(request):
    nombre = request.POST.get('nombre')
    if not nombre:
        return JsonResponse({'error': 'Nombre requerido'}, status=400)
    mecanico, created = Mecanico.objects.get_or_create(nombre=nombre)
    return JsonResponse({'id': mecanico.id, 'nombre': mecanico.nombre})
from django.views.decorators.http import require_GET

# --- AUTOCOMPLETE REPUESTO ---
@require_GET
def autocomplete_repuesto(request):
    from taller.models.repuesto import Repuesto
    q = request.GET.get('q', '')
    repuestos = Repuesto.objects.filter(part_number__icontains=q)[:10]
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
def autocomplete_servicio_nombre(request):
    from taller.servicios.models import Servicio
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

def obtener_vehiculos_por_cliente(request):
    cliente_id = request.GET.get('cliente_id')
    if not cliente_id:
        return JsonResponse({'error': 'cliente_id requerido'}, status=400)
    vehiculos = Vehiculo.objects.filter(cliente_id=cliente_id).values('id', 'patente', 'marca__nombre', 'modelo__nombre')
    return JsonResponse(list(vehiculos), safe=False)

def autocomplete_servicio(request):
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

 

def crear_documento(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST)
        if form.is_valid():
            documento = form.save(commit=False)

            # Generar número de documento si no está asignado
            if not documento.numero_documento:
                tipo = documento.tipo_documento.lower().replace(" ", "_")
                count = Documento.objects.filter(tipo_documento=documento.tipo_documento).count() + 1
                documento.numero_documento = f"{tipo[:3].upper()}-{count:05d}"

            documento.save()
            form.save_m2m()

            # Procesar ítems desde JSON (repuestos y servicios) para cualquier tipo de documento
            json_items = request.POST.get('json_items')
            if json_items is not None:
                try:
                    items = json.loads(json_items)
                    from taller.models.documento import RepuestoDocumento, ServicioDocumento
                    for item in items:
                        if not item.get('nombre') or float(item.get('precio', 0)) <= 0:
                            continue
                        if item.get('tipo') == 'repuesto':
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item.get('partnumber', ''),
                                nombre=item['nombre'],
                                cantidad=item.get('cantidad', 1),
                                precio=item['precio']
                            )
                        elif item.get('tipo') == 'servicio':
                            ServicioDocumento.objects.create(
                                documento=documento,
                                nombre=item['nombre'],
                                precio=item['precio']
                            )
                except Exception as e:
                    print(f"❌ Error procesando ítems: {e}")

            return redirect('documentos:lista_documentos')
    else:
        from datetime import date
        hoy = date.today().strftime('%Y-%m-%d')
        form = DocumentoForm(initial={'fecha': hoy})

    return render(request, 'taller/documentos/crear_documento.html', {
        'form': form,
    })

def ver_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    repuestos = documento.repuestos.all()
    servicios = documento.servicios.all()
    subtotal_repuestos = sum(r.total for r in repuestos)
    subtotal_servicios = sum(s.precio for s in servicios)
    subtotal = subtotal_repuestos + subtotal_servicios
    iva = subtotal * 0.19
    total = subtotal + iva

    return render(request, 'taller/documentos/ver_documento.html', {
        'documento': documento,
        'repuestos': repuestos,
        'servicios': servicios,
        'subtotal': subtotal,
        'iva': iva,
        'total': total
    })



def lista_documentos(request):
    documentos = Documento.objects.all()
    return render(request, 'taller/documentos/lista_documentos.html', {'documentos': documentos})


def editar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    if request.method == 'POST':
        form = DocumentoForm(request.POST, instance=documento)
        if form.is_valid():
            documento = form.save()

            # Procesar ítems desde JSON (repuestos y servicios)
            json_items = request.POST.get('json_items')
            if json_items is not None:
                try:
                    items = json.loads(json_items)
                    from taller.models.documento import RepuestoDocumento, ServicioDocumento
                    # Eliminar los repuestos y servicios anteriores
                    documento.repuestos.all().delete()
                    documento.servicios.all().delete()
                    for item in items:
                        if not item.get('nombre') or float(item.get('precio', 0)) <= 0:
                            continue
                        if item.get('tipo') == 'repuesto':
                            RepuestoDocumento.objects.create(
                                documento=documento,
                                codigo=item.get('partnumber', ''),
                                nombre=item['nombre'],
                                cantidad=item.get('cantidad', 1),
                                precio=item['precio']
                            )
                        elif item.get('tipo') == 'servicio':
                            ServicioDocumento.objects.create(
                                documento=documento,
                                nombre=item['nombre'],
                                precio=item['precio']
                            )
                except Exception as e:
                    print(f"❌ Error procesando ítems al editar: {e}")

            # Redirigir a la misma página de edición para mantener los datos y mostrar el mecánico seleccionado
            return redirect('documentos:editar_documento', documento_id=documento.id)
    else:
        form = DocumentoForm(instance=documento)
    servicios = documento.servicios.all()
    repuestos = documento.repuestos.all()
    return render(request, 'taller/documentos/formulario_documento.html', {
        'form': form,
        'servicios': servicios,
        'repuestos': repuestos,
    })


def eliminar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    documento.delete()
    return redirect('lista_documentos')


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
def numero_documento_auto(request):
    tipo = request.GET.get("tipo")
    if not tipo:
        return JsonResponse({"error": "Tipo no proporcionado"}, status=400)

    count = Documento.objects.filter(tipo_documento=tipo).count() + 1
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
