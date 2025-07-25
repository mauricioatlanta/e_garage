"""
Vistas para exportación de documentos y reportes
"""
import json
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from datetime import datetime, timedelta
from taller.models.documento import Documento
from taller.utils.export_utils import (
    DocumentoPDFExporter, 
    ReportesExcelExporter, 
    WhatsAppSender, 
    EmailSender
)


@login_required
@require_http_methods(["GET"])
def exportar_documento_pdf(request, documento_id):
    """Exporta un documento individual a PDF"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=request.user.perfilusuario.empresa)
    
    try:
        exporter = DocumentoPDFExporter(documento)
        response = exporter.generar_response_pdf()
        
        # Registrar la exportación (opcional)
        # LogExportacion.objects.create(
        #     documento=documento,
        #     tipo_exportacion='PDF',
        #     usuario=request.user,
        #     fecha=datetime.now()
        # )
        
        return response
    except Exception as e:
        messages.error(request, f"Error al generar PDF: {str(e)}")
        return redirect('documentos:detalle', documento_id=documento_id)


@login_required
@require_http_methods(["GET"])
def exportar_rentabilidad_excel(request):
    """Exporta reporte de rentabilidad a Excel"""
    empresa = request.user.perfilusuario.empresa
    
    # Obtener parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Convertir fechas si se proporcionan
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    try:
        exporter = ReportesExcelExporter(empresa, fecha_inicio, fecha_fin)
        response = exporter.exportar_rentabilidad_mensual()
        
        return response
    except Exception as e:
        messages.error(request, f"Error al generar Excel: {str(e)}")
        return redirect('reportes_dashboard')


@login_required
@require_http_methods(["POST"])
def enviar_documento_whatsapp(request, documento_id):
    """Genera enlace de WhatsApp para enviar documento"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=request.user.perfilusuario.empresa)
    
    try:
        # Verificar que el cliente tenga teléfono
        if not documento.cliente.telefono:
            return JsonResponse({
                'success': False, 
                'error': 'El cliente no tiene número de teléfono registrado'
            })
        
        # Generar PDF temporal (opcional, para link)
        # En producción, podrías generar un enlace temporal al PDF
        
        # Crear mensaje personalizado
        fecha_str = documento.fecha.strftime('%d/%m/%Y') if documento.fecha else 'N/A'
        vehiculo_info = f"{documento.vehiculo.marca} {documento.vehiculo.modelo}" if documento.vehiculo else 'N/A'
        
        mensaje = f"""Hola {documento.cliente.nombre}!
        
Te enviamos tu {documento.tipo_documento.lower()} #{documento.numero_documento} de {documento.empresa.nombre}.

Fecha: {fecha_str}
Vehículo: {vehiculo_info}

¡Gracias por confiar en nosotros!"""
        
        # Generar enlace de WhatsApp
        enlace_whatsapp = WhatsAppSender.generar_enlace_whatsapp(
            documento.cliente.telefono, 
            mensaje
        )
        
        return JsonResponse({
            'success': True,
            'enlace_whatsapp': enlace_whatsapp,
            'mensaje': 'Enlace de WhatsApp generado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al generar enlace: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def enviar_documento_email(request, documento_id):
    """Envía documento por email"""
    documento = get_object_or_404(Documento, id=documento_id, empresa=request.user.perfilusuario.empresa)
    
    try:
        data = json.loads(request.body)
        email_destinatario = data.get('email', documento.cliente.email)
        incluir_pdf = data.get('incluir_pdf', True)
        
        if not email_destinatario:
            return JsonResponse({
                'success': False,
                'error': 'No se ha proporcionado email de destino'
            })
        
        # Enviar email
        resultado = EmailSender.enviar_documento_por_email(
            documento, 
            email_destinatario, 
            adjuntar_pdf=incluir_pdf
        )
        
        if resultado:
            # Registrar el envío (opcional)
            # LogEnvio.objects.create(
            #     documento=documento,
            #     tipo_envio='EMAIL',
            #     destinatario=email_destinatario,
            #     usuario=request.user,
            #     fecha=datetime.now(),
            #     exitoso=True
            # )
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Email enviado correctamente a {email_destinatario}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al enviar el email'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al enviar email: {str(e)}'
        })


@login_required
@require_http_methods(["GET"])
def vista_impresion_documento(request, documento_id):
    """Vista optimizada para impresión de documento"""
    from django.shortcuts import render
    
    documento = get_object_or_404(Documento, id=documento_id, empresa=request.user.perfilusuario.empresa)
    
    # Calcular totales
    total_repuestos = sum(r.total for r in documento.repuestos.all())
    total_servicios = sum(s.precio for s in documento.servicios.all())
    total_otros_servicios = sum(os.precio_cliente for os in documento.otros_servicios.all())
    
    subtotal = total_repuestos + total_servicios + total_otros_servicios
    iva = subtotal * 0.19 if documento.incluir_iva else 0
    total = subtotal + iva
    
    context = {
        'documento': documento,
        'repuestos': documento.repuestos.all(),
        'servicios': documento.servicios.all(),
        'otros_servicios': documento.otros_servicios.all(),
        'total_repuestos': total_repuestos,
        'total_servicios': total_servicios,
        'total_otros_servicios': total_otros_servicios,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
        'empresa': documento.empresa,
        'fecha_generacion': datetime.now(),
    }
    
    return render(request, 'taller/documentos/vista_impresion.html', context)


@login_required
@require_http_methods(["GET"])
def exportar_dashboard_imagen(request):
    """Endpoint para exportar dashboard como imagen (usando JavaScript)"""
    # Esta vista será llamada desde JavaScript después de generar la imagen
    return JsonResponse({
        'success': True,
        'mensaje': 'Función disponible desde el frontend con html2canvas'
    })
