# taller/reportes/exporters.py
"""
Exportadores especializados para reportes de mecánicos
"""

from django.http import HttpResponse
from django.template.loader import get_template
from datetime import date, timedelta
from taller.models.documento import Documento, ServicioDocumento
from taller.models.mecanico import Mecanico
from django.db.models import Sum, Count
import io


def generar_pdf_mecanico(mecanico_id, fecha_desde=None, fecha_hasta=None):
    """
    Genera un PDF personalizado para un mecánico específico
    """
    try:
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string
        
        mecanico = Mecanico.objects.get(id=mecanico_id)
        
        # Fechas por defecto
        if not fecha_desde:
            fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not fecha_hasta:
            fecha_hasta = date.today().strftime('%Y-%m-%d')
        
        # Obtener datos del mecánico
        documentos = Documento.objects.filter(
            mecanico=mecanico,
            fecha__range=[fecha_desde, fecha_hasta]
        )
        
        servicios = ServicioDocumento.objects.filter(documento__in=documentos)
        total_generado = servicios.aggregate(Sum('precio'))['precio__sum'] or 0
        
        # Servicios más realizados
        servicios_top = (
            servicios
            .values('nombre')
            .annotate(cantidad=Count('id'), total_ingresos=Sum('precio'))
            .order_by('-cantidad')[:10]
        )
        
        # Documentos por tipo
        docs_por_tipo = (
            documentos
            .values('tipo_documento')
            .annotate(cantidad=Count('id'), total=Sum('servicios__precio'))
            .order_by('-cantidad')
        )
        
        context = {
            'mecanico': mecanico,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'total_documentos': documentos.count(),
            'total_servicios': servicios.count(),
            'total_generado': total_generado,
            'promedio_documento': round(total_generado / documentos.count() if documentos.count() > 0 else 0, 0),
            'servicios_top': servicios_top,
            'docs_por_tipo': docs_por_tipo,
            'fecha_generacion': date.today().strftime('%d/%m/%Y'),
        }
        
        # Renderizar HTML
        html_string = render_to_string('taller/reportes/pdf_mecanico.html', context)
        
        # CSS personalizado
        css_string = """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "Reporte Individual - """ + mecanico.nombre + """";
                font-family: Arial, sans-serif;
                font-size: 12px;
                color: #666;
            }
            @bottom-center {
                content: "Página " counter(page) " de " counter(pages);
                font-family: Arial, sans-serif;
                font-size: 10px;
                color: #666;
            }
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #f0f8ff, #e6f3ff);
            border-radius: 10px;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 24px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-box {
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            border-radius: 5px;
        }
        .metric-value {
            font-size: 20px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #6c757d;
            font-size: 12px;
            text-transform: uppercase;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 8px;
            border: 1px solid #dee2e6;
            text-align: left;
        }
        th {
            background: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }
        .footer {
            margin-top: 40px;
            text-align: center;
            color: #6c757d;
            font-size: 10px;
        }
        """
        
        # Generar PDF
        html = HTML(string=html_string, base_url='.')
        css = CSS(string=css_string)
        pdf = html.write_pdf(stylesheets=[css])
        
        return pdf
        
    except ImportError:
        # Si WeasyPrint no está disponible, generar HTML simple
        from django.template.loader import render_to_string
        
        context = {
            'mecanico': Mecanico.objects.get(id=mecanico_id),
            'error': 'WeasyPrint no está instalado. Instalalo con: pip install weasyprint'
        }
        
        return render_to_string('taller/reportes/pdf_simple.html', context)


def exportar_csv_personalizado(mecanico_id=None, fecha_desde=None, fecha_hasta=None):
    """
    Exporta datos de mecánicos en formato CSV personalizado
    """
    import csv
    from io import StringIO
    
    # Configurar filtros
    if not fecha_desde:
        fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = date.today().strftime('%Y-%m-%d')
    
    documentos_qs = Documento.objects.filter(
        fecha__range=[fecha_desde, fecha_hasta],
        mecanico__isnull=False
    )
    
    if mecanico_id:
        documentos_qs = documentos_qs.filter(mecanico_id=mecanico_id)
    
    # Crear CSV en memoria
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Fecha',
        'Mecánico',
        'Tipo Documento',
        'Número Documento',
        'Cliente',
        'Vehículo',
        'Servicios',
        'Total Generado',
        'Observaciones'
    ])
    
    # Datos
    for documento in documentos_qs:
        servicios = ServicioDocumento.objects.filter(documento=documento)
        total_servicios = servicios.aggregate(Sum('precio'))['precio__sum'] or 0
        servicios_nombres = ', '.join(servicios.values_list('nombre', flat=True)[:3])
        
        writer.writerow([
            documento.fecha.strftime('%d/%m/%Y') if documento.fecha else '',
            documento.mecanico.nombre if documento.mecanico else '',
            documento.tipo_documento,
            documento.numero_documento or '',
            str(documento.cliente) if documento.cliente else '',
            f"{documento.vehiculo.patente} - {documento.vehiculo.modelo}" if documento.vehiculo else '',
            servicios_nombres,
            total_servicios,
            documento.observaciones or ''
        ])
    
    return output.getvalue()


def generar_estadisticas_avanzadas(fecha_desde=None, fecha_hasta=None):
    """
    Genera estadísticas avanzadas para análisis gerencial
    """
    if not fecha_desde:
        fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = date.today().strftime('%Y-%m-%d')
    
    documentos_qs = Documento.objects.filter(
        fecha__range=[fecha_desde, fecha_hasta],
        mecanico__isnull=False
    )
    
    # Estadísticas por mecánico
    estadisticas = {}
    
    for mecanico in Mecanico.objects.all():
        docs_mecanico = documentos_qs.filter(mecanico=mecanico)
        servicios_mecanico = ServicioDocumento.objects.filter(documento__in=docs_mecanico)
        
        total_docs = docs_mecanico.count()
        total_servicios = servicios_mecanico.count()
        total_generado = servicios_mecanico.aggregate(Sum('precio'))['precio__sum'] or 0
        
        if total_docs > 0:
            # Calcular métricas avanzadas
            promedio_doc = total_generado / total_docs
            promedio_servicio = total_generado / total_servicios if total_servicios > 0 else 0
            
            # Servicios únicos realizados
            servicios_unicos = servicios_mecanico.values('nombre').distinct().count()
            
            # Tipos de documentos
            tipos_docs = docs_mecanico.values('tipo_documento').annotate(count=Count('id'))
            
            estadisticas[mecanico.id] = {
                'mecanico': mecanico.nombre,
                'total_documentos': total_docs,
                'total_servicios': total_servicios,
                'servicios_unicos': servicios_unicos,
                'total_generado': total_generado,
                'promedio_por_documento': round(promedio_doc, 0),
                'promedio_por_servicio': round(promedio_servicio, 0),
                'tipos_documentos': list(tipos_docs),
                'eficiencia': round((total_servicios / total_docs) if total_docs > 0 else 0, 2)
            }
    
    return estadisticas


class ReporteMecanicoWhatsApp:
    """
    Clase para generar reportes personalizados por WhatsApp
    """
    
    @staticmethod
    def generar_resumen_semanal(mecanico_id):
        """Genera resumen semanal para WhatsApp"""
        mecanico = Mecanico.objects.get(id=mecanico_id)
        fecha_desde = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_hasta = date.today().strftime('%Y-%m-%d')
        
        documentos = Documento.objects.filter(
            mecanico=mecanico,
            fecha__range=[fecha_desde, fecha_hasta]
        )
        
        servicios = ServicioDocumento.objects.filter(documento__in=documentos)
        total_generado = servicios.aggregate(Sum('precio'))['precio__sum'] or 0
        
        # Servicios top
        servicios_top = (
            servicios
            .values('nombre')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')[:3]
        )
        
        mensaje = f"""🔧 *RESUMEN SEMANAL - {mecanico.nombre.upper()}*

📅 *Período:* Últimos 7 días

📊 *MÉTRICAS:*
• Documentos: {documentos.count()}
• Servicios: {servicios.count()}
• Total generado: ${total_generado:,.0f}
• Promedio/doc: ${(total_generado / documentos.count() if documentos.count() > 0 else 0):,.0f}

🏆 *TUS ESPECIALIDADES:*"""
        
        for i, servicio in enumerate(servicios_top, 1):
            mensaje += f"\n{i}. {servicio['nombre']} ({servicio['cantidad']}x)"
        
        mensaje += "\n\n💪 ¡Sigue así!"
        mensaje += "\n_Reporte automático eGarage_"
        
        return mensaje
    
    @staticmethod
    def generar_resumen_mensual(mecanico_id):
        """Genera resumen mensual para WhatsApp"""
        mecanico = Mecanico.objects.get(id=mecanico_id)
        fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_hasta = date.today().strftime('%Y-%m-%d')
        
        documentos = Documento.objects.filter(
            mecanico=mecanico,
            fecha__range=[fecha_desde, fecha_hasta]
        )
        
        servicios = ServicioDocumento.objects.filter(documento__in=documentos)
        total_generado = servicios.aggregate(Sum('precio'))['precio__sum'] or 0
        
        # Comparar con mes anterior
        fecha_mes_anterior_inicio = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')
        fecha_mes_anterior_fin = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        documentos_anterior = Documento.objects.filter(
            mecanico=mecanico,
            fecha__range=[fecha_mes_anterior_inicio, fecha_mes_anterior_fin]
        )
        
        servicios_anterior = ServicioDocumento.objects.filter(documento__in=documentos_anterior)
        total_anterior = servicios_anterior.aggregate(Sum('precio'))['precio__sum'] or 0
        
        # Calcular crecimiento
        crecimiento = 0
        if total_anterior > 0:
            crecimiento = round(((total_generado - total_anterior) / total_anterior) * 100, 1)
        
        emoji_tendencia = "📈" if crecimiento > 0 else "📉" if crecimiento < 0 else "➡️"
        
        mensaje = f"""📊 *RESUMEN MENSUAL - {mecanico.nombre.upper()}*

📅 *Período:* Últimos 30 días

💰 *RESULTADOS:*
• Total generado: ${total_generado:,.0f}
• Documentos: {documentos.count()}
• Servicios: {servicios.count()}

{emoji_tendencia} *TENDENCIA:*
• Mes anterior: ${total_anterior:,.0f}
• Crecimiento: {crecimiento:+.1f}%

🎯 *PRÓXIMO OBJETIVO:*
• Meta sugerida: ${int(total_generado * 1.1):,.0f}

🏆 ¡Excelente trabajo!
_Reporte eGarage Pro_"""
        
        return mensaje
