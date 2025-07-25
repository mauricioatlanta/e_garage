"""
Vistas para exportación de documentos y reportes
"""
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from taller.models.documento import Documento
from taller.utils.export_utils import DocumentoPDFExporter, ReportesExcelExporter, WhatsAppSender, EmailSender
from taller.middleware.trial_middleware import empresa_actual
import json
from datetime import datetime, timedelta
from django.utils import timezone


@login_required
def exportar_documento_pdf(request, documento_id):
    """Exporta un documento específico a PDF"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa_actual(request))
    
    try:
        exporter = DocumentoPDFExporter(documento)
        response = exporter.generar_response_pdf()
        
        # Log de exportación (opcional)
        messages.success(request, f"PDF generado exitosamente para {documento.tipo_documento} #{documento.numero_documento}")
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar PDF: {str(e)}")
        return HttpResponse("Error al generar PDF", status=500)


@login_required
def enviar_documento_email(request, documento_id):
    """Envía un documento por email"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa_actual(request))
    
    if request.method == 'POST':
        email_destinatario = request.POST.get('email')
        mensaje_personalizado = request.POST.get('mensaje', '')
        
        if not email_destinatario:
            return JsonResponse({'error': 'Email requerido'}, status=400)
        
        try:
            # Enviar email
            resultado = EmailSender.enviar_documento_por_email(
                documento=documento,
                email_destinatario=email_destinatario,
                adjuntar_pdf=True
            )
            
            if resultado:
                messages.success(request, f"Documento enviado exitosamente a {email_destinatario}")
                return JsonResponse({'success': True, 'message': 'Email enviado correctamente'})
            else:
                return JsonResponse({'error': 'Error al enviar email'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    
    # GET: Mostrar formulario
    context = {
        'documento': documento,
        'email_sugerido': documento.cliente.email if documento.cliente.email else '',
    }
    return render(request, 'taller/documentos/enviar_email_form.html', context)


@login_required
def generar_link_whatsapp(request, documento_id):
    """Genera link de WhatsApp para enviar documento"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa_actual(request))
    
    telefono = request.GET.get('telefono') or documento.cliente.telefono
    
    if not telefono:
        return JsonResponse({'error': 'Número de teléfono requerido'}, status=400)
    
    try:
        # Generar URL temporal del documento (válida por 48 horas)
        documento_url = request.build_absolute_uri(
            reverse('exportar_documento_pdf', kwargs={'documento_id': documento.id})
        )
        
        # Mensaje personalizado
        mensaje = f"""¡Hola {documento.cliente.nombre}! 

Adjunto encontrarás tu {documento.tipo_documento.lower()} #{documento.numero_documento} de {documento.empresa.nombre}.

📋 Detalle:
• Vehículo: {documento.vehiculo.marca} {documento.vehiculo.modelo if documento.vehiculo else 'N/A'}
• Fecha: {documento.fecha.strftime('%d/%m/%Y')}

¡Gracias por confiar en nosotros! 🚗✨"""
        
        # Generar link de WhatsApp
        whatsapp_link = WhatsAppSender.generar_enlace_whatsapp(
            telefono=telefono,
            mensaje=mensaje,
            archivo_url=documento_url
        )
        
        return JsonResponse({
            'success': True,
            'whatsapp_link': whatsapp_link,
            'telefono': telefono,
            'mensaje': mensaje
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@login_required
def exportar_rentabilidad_excel(request):
    """Exporta reporte de rentabilidad a Excel"""
    empresa = empresa_actual(request)
    
    # Obtener parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Fechas por defecto (último mes)
    if not fecha_inicio or not fecha_fin:
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Formato de fecha inválido")
            return HttpResponse("Error en formato de fecha", status=400)
    
    try:
        exporter = ReportesExcelExporter(empresa, fecha_inicio, fecha_fin)
        response = exporter.exportar_rentabilidad_mensual()
        
        messages.success(request, f"Reporte Excel generado para el período {fecha_inicio} - {fecha_fin}")
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar Excel: {str(e)}")
        return HttpResponse("Error al generar Excel", status=500)


@login_required
@require_http_methods(["POST"])
def vista_previa_documento(request, documento_id):
    """Genera vista previa del documento en formato JSON"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa_actual(request))
    
    try:
        # Calcular totales
        total_repuestos = sum(item.total for item in documento.repuestos.all())
        total_servicios = sum(servicio.precio for servicio in documento.servicios.all())
        total_otros_servicios = sum(servicio.precio_cliente for servicio in documento.otros_servicios.all())
        
        subtotal = total_repuestos + total_servicios + total_otros_servicios
        iva = subtotal * 0.19 if documento.incluir_iva else 0
        total_final = subtotal + iva
        
        # Preparar datos para vista previa
        vista_previa = {
            'documento': {
                'tipo': documento.tipo_documento,
                'numero': documento.numero_documento,
                'fecha': documento.fecha.strftime('%d/%m/%Y'),
            },
            'cliente': {
                'nombre': documento.cliente.nombre,
                'rut': documento.cliente.rut or '',
                'telefono': documento.cliente.telefono or '',
                'email': documento.cliente.email or '',
            },
            'vehiculo': {
                'marca': documento.vehiculo.marca if documento.vehiculo else '',
                'modelo': documento.vehiculo.modelo if documento.vehiculo else '',
                'patente': documento.vehiculo.patente if documento.vehiculo else '',
            } if documento.vehiculo else None,
            'totales': {
                'repuestos': float(total_repuestos),
                'servicios': float(total_servicios),
                'otros_servicios': float(total_otros_servicios),
                'subtotal': float(subtotal),
                'iva': float(iva),
                'total': float(total_final),
            },
            'items': {
                'repuestos_count': documento.repuestos.count(),
                'servicios_count': documento.servicios.count(),
                'otros_servicios_count': documento.otros_servicios.count(),
            }
        }
        
        return JsonResponse({'success': True, 'data': vista_previa})
        
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@login_required
def opciones_entrega_documento(request, documento_id):
    """Muestra opciones de entrega para un documento"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa_actual(request))
    
    context = {
        'documento': documento,
        'cliente': documento.cliente,
        'empresa': documento.empresa,
        'tiene_email': bool(documento.cliente.email),
        'tiene_telefono': bool(documento.cliente.telefono),
        'pdf_url': reverse('exportar_documento_pdf', kwargs={'documento_id': documento.id}),
        'email_url': reverse('enviar_documento_email', kwargs={'documento_id': documento.id}),
        'whatsapp_url': reverse('generar_link_whatsapp', kwargs={'documento_id': documento.id}),
    }
    
    return render(request, 'taller/documentos/opciones_entrega.html', context)


@login_required
def dashboard_exportaciones(request):
    """Dashboard con opciones de exportación"""
    empresa = empresa_actual(request)
    
    # Estadísticas rápidas
    documentos_mes_actual = Documento.objects.filter(
        empresa=empresa,
        fecha__month=timezone.now().month,
        fecha__year=timezone.now().year
    ).count()
    
    context = {
        'empresa': empresa,
        'documentos_mes_actual': documentos_mes_actual,
        'fecha_actual': timezone.now().date(),
        'excel_url': reverse('exportar_rentabilidad_excel'),
    }
    
    return render(request, 'taller/exports/dashboard.html', context)
