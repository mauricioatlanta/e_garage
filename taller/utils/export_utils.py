"""
Utilidades para exportación de documentos a PDF, Excel y otros formatos
"""
import io
import os
from django.http import HttpResponse, FileResponse
from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML, CSS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import pandas as pd
from datetime import datetime
from decimal import Decimal


class DocumentoPDFExporter:
    """Clase para exportar documentos a PDF con formato profesional"""
    
    def __init__(self, documento):
        self.documento = documento
        
    def generar_pdf(self):
        """Genera un PDF del documento completo"""
        # Template HTML para el PDF
        template = get_template('taller/documentos/pdf_template.html')
        
        # Contexto con todos los datos del documento
        context = {
            'documento': self.documento,
            'repuestos': self.documento.repuestos.all(),
            'servicios': self.documento.servicios.all(),
            'otros_servicios': self.documento.otros_servicios.all(),
            'total_repuestos': sum(r.total for r in self.documento.repuestos.all()),
            'total_servicios': sum(s.precio for s in self.documento.servicios.all()),
            'total_otros_servicios': sum(os.precio_cliente for os in self.documento.otros_servicios.all()),
            'fecha_generacion': datetime.now(),
            'empresa': self.documento.empresa,
        }
        
        # Calcular totales
        subtotal = context['total_repuestos'] + context['total_servicios'] + context['total_otros_servicios']
        iva = subtotal * Decimal('0.19') if self.documento.incluir_iva else 0
        total = subtotal + iva
        
        context.update({
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
        })
        
        # Renderizar HTML
        html_string = template.render(context)
        
        # Generar PDF con WeasyPrint
        html = HTML(string=html_string)
        css = CSS(string="""
            @page {
                size: A4;
                margin: 1cm;
                @bottom-center {
                    content: "Página " counter(page) " de " counter(pages);
                }
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            .logo {
                max-height: 80px;
                margin-bottom: 10px;
            }
            .info-section {
                margin-bottom: 15px;
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }
            .table th, .table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .table th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .totals {
                float: right;
                width: 300px;
                margin-top: 20px;
            }
            .totals table {
                width: 100%;
            }
            .footer {
                margin-top: 50px;
                text-align: center;
                border-top: 1px solid #ddd;
                padding-top: 10px;
                font-size: 10px;
                color: #666;
            }
        """)
        
        pdf_file = html.write_pdf(stylesheets=[css])
        
        return pdf_file
    
    def generar_response_pdf(self):
        """Genera una respuesta HTTP con el PDF"""
        pdf_file = self.generar_pdf()
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f"{self.documento.tipo_documento}_{self.documento.numero_documento}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class ReportesExcelExporter:
    """Clase para exportar reportes a Excel"""
    
    def __init__(self, empresa, fecha_inicio=None, fecha_fin=None):
        self.empresa = empresa
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
    
    def exportar_rentabilidad_mensual(self):
        """Exporta reporte de rentabilidad mensual a Excel"""
        from taller.models.documento import Documento
        
        # Filtrar documentos
        documentos = Documento.objects.filter(empresa=self.empresa)
        if self.fecha_inicio and self.fecha_fin:
            documentos = documentos.filter(fecha__range=[self.fecha_inicio, self.fecha_fin])
        
        # Crear DataFrame
        data = []
        for doc in documentos:
            total_repuestos = sum(r.total for r in doc.repuestos.all())
            total_servicios = sum(s.precio for s in doc.servicios.all())
            total_otros_servicios = sum(os.precio_cliente for os in doc.otros_servicios.all())
            costos_externos = sum(os.costo_interno for os in doc.otros_servicios.all())
            ganancia_externa = sum(os.ganancia for os in doc.otros_servicios.all())
            
            subtotal = total_repuestos + total_servicios + total_otros_servicios
            total = subtotal * Decimal('1.19') if doc.incluir_iva else subtotal
            
            data.append({
                'Fecha': doc.fecha,
                'Tipo Documento': doc.tipo_documento,
                'Número': doc.numero_documento,
                'Cliente': str(doc.cliente),
                'Vehículo': str(doc.vehiculo) if doc.vehiculo else '',
                'Total Repuestos': float(total_repuestos),
                'Total Servicios Internos': float(total_servicios),
                'Total Servicios Externos': float(total_otros_servicios),
                'Costos Externos': float(costos_externos),
                'Ganancia Servicios Externos': float(ganancia_externa),
                'Subtotal': float(subtotal),
                'Total con IVA': float(total),
                'Margen Servicios Externos %': round((ganancia_externa / total_otros_servicios * 100) if total_otros_servicios > 0 else 0, 2)
            })
        
        # Crear Excel
        df = pd.DataFrame(data)
        
        # Crear buffer
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Rentabilidad', index=False)
            
            # Obtener el workbook y worksheet
            workbook = writer.book
            worksheet = writer.sheets['Rentabilidad']
            
            # Estilos
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='007bff', end_color='007bff', fill_type='solid')
            
            # Aplicar estilos a headers
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Crear respuesta
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'rentabilidad_{self.empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class WhatsAppSender:
    """Utilidades para envío por WhatsApp"""
    
    @staticmethod
    def generar_enlace_whatsapp(telefono, mensaje, archivo_url=None):
        """Genera enlace de WhatsApp con mensaje predefinido"""
        import urllib.parse
        
        # Limpiar número de teléfono
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        if telefono_limpio.startswith('9'):
            telefono_limpio = '56' + telefono_limpio
        elif not telefono_limpio.startswith('56'):
            telefono_limpio = '56' + telefono_limpio
        
        # Crear mensaje
        if archivo_url:
            mensaje_completo = f"{mensaje}\n\nPuedes descargar tu documento aquí: {archivo_url}"
        else:
            mensaje_completo = mensaje
        
        mensaje_encoded = urllib.parse.quote(mensaje_completo)
        
        return f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"


class EmailSender:
    """Utilidades para envío por email"""
    
    @staticmethod
    def enviar_documento_por_email(documento, email_destinatario, adjuntar_pdf=True):
        """Envía documento por email"""
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        
        # Generar PDF si se solicita
        pdf_content = None
        if adjuntar_pdf:
            exporter = DocumentoPDFExporter(documento)
            pdf_content = exporter.generar_pdf()
        
        # Preparar email
        subject = f"{documento.tipo_documento} #{documento.numero_documento} - {documento.empresa.nombre}"
        
        # Renderizar template del email
        email_context = {
            'documento': documento,
            'cliente': documento.cliente,
            'empresa': documento.empresa,
        }
        
        html_message = render_to_string('taller/emails/documento_email.html', email_context)
        text_message = render_to_string('taller/emails/documento_email.txt', email_context)
        
        # Crear email
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destinatario],
        )
        
        if html_message:
            email.attach_alternative(html_message, "text/html")
        
        # Adjuntar PDF
        if pdf_content:
            filename = f"{documento.tipo_documento}_{documento.numero_documento}.pdf"
            email.attach(filename, pdf_content, 'application/pdf')
        
        # Enviar
        return email.send()
