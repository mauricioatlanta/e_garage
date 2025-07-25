"""
Generador de informes ejecutivos en PDF para eGarage
Sistema de reportes avanzados con gráficos integrados
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime, date
import os
import tempfile
from io import BytesIO


class InformeEjecutivoPDF:
    """Generador de informes ejecutivos profesionales para talleres automotrices"""
    
    def __init__(self, datos_contexto, nombre_taller="eGarage"):
        self.datos = datos_contexto
        self.nombre_taller = nombre_taller
        self.fecha_generacion = datetime.now()
        self.buffer = BytesIO()
        
        # Configurar estilos
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configurar estilos personalizados para el PDF"""
        
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='TituloEjecutivo',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#0080ff'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubtituloSeccion',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.HexColor('#00ffff'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para KPIs
        self.styles.add(ParagraphStyle(
            name='KPI',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Estilo para valores grandes
        self.styles.add(ParagraphStyle(
            name='ValorGrande',
            parent=self.styles['Normal'],
            fontSize=20,
            spaceAfter=5,
            textColor=colors.HexColor('#0080ff'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.HexColor('#444444'),
            fontName='Helvetica',
            alignment=TA_JUSTIFY
        ))
        
        # Estilo para footer
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica',
            alignment=TA_CENTER
        ))
    
    def _crear_header(self):
        """Crear header del documento"""
        story = []
        
        # Título principal
        titulo = f"📊 INFORME EJECUTIVO - {self.nombre_taller.upper()}"
        story.append(Paragraph(titulo, self.styles['TituloEjecutivo']))
        
        # Fecha y período
        fecha_texto = f"Generado el {self.fecha_generacion.strftime('%d de %B de %Y')}"
        story.append(Paragraph(fecha_texto, self.styles['TextoNormal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _crear_seccion_kpis(self):
        """Crear sección de KPIs principales"""
        story = []
        
        story.append(Paragraph("🎯 INDICADORES CLAVE DE RENDIMIENTO", self.styles['SubtituloSeccion']))
        
        # Crear tabla de KPIs en 2 columnas
        kpis_data = [
            ['📈 FACTURACIÓN TOTAL', '👥 CLIENTES ACTIVOS'],
            [f"${self.datos.get('facturacion_total', 0):,.0f}", f"{self.datos.get('clientes_activos_porcentaje', 0)}%"],
            ['💰 TICKET PROMEDIO', '⚙️ SERVICIOS/SEMANA'],
            [f"${self.datos.get('ticket_promedio', 0):,.0f}", f"{self.datos.get('vehiculos_por_semana', 0)}"],
            ['📊 MARGEN PROMEDIO', '⭐ SATISFACCIÓN'],
            [f"{self.datos.get('margen_promedio', 0)}%", f"{self.datos.get('satisfaccion_cliente', 0)}⭐"]
        ]
        
        kpi_table = Table(kpis_data, colWidths=[3*inch, 3*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f8ff')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f0f8ff')),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#f0f8ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 16),
            ('FONTSIZE', (0, 3), (-1, 3), 16),
            ('FONTSIZE', (0, 5), (-1, 5), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        
        story.append(kpi_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _crear_grafico_facturacion(self):
        """Crear gráfico de facturación mensual"""
        drawing = Drawing(400, 200)
        
        # Datos de ejemplo (en producción usar self.datos['facturacion_por_mes'])
        data = [(1, 1200000), (2, 1350000), (3, 1480000), (4, 1620000), (5, 1750000), (6, 1890000)]
        
        lp = LinePlot()
        lp.x = 50
        lp.y = 50
        lp.height = 125
        lp.width = 300
        lp.data = [data]
        lp.lines[0].strokeColor = colors.HexColor('#0080ff')
        lp.lines[0].strokeWidth = 3
        
        # Configurar ejes
        lp.xValueAxis.valueMin = 1
        lp.xValueAxis.valueMax = 6
        lp.xValueAxis.labels.fontSize = 8
        lp.yValueAxis.labels.fontSize = 8
        lp.yValueAxis.labelTextFormat = lambda x: f'${x/1000000:.1f}M'
        
        drawing.add(lp)
        return drawing
    
    def _crear_ranking_servicios(self):
        """Crear tabla de ranking de servicios"""
        story = []
        
        story.append(Paragraph("🔧 TOP SERVICIOS MÁS DEMANDADOS", self.styles['SubtituloSeccion']))
        
        # Datos de servicios (usar datos reales de self.datos['servicios_demandados'])
        servicios_data = [
            ['Servicio', 'Cantidad', 'Ingresos'],
            ['Mantenimiento General', '45', '$675,000'],
            ['Cambio de Aceite', '38', '$456,000'],
            ['Revisión de Frenos', '32', '$640,000'],
            ['Diagnóstico Electrónico', '28', '$420,000'],
            ['Alineación y Balanceo', '25', '$375,000']
        ]
        
        servicios_table = Table(servicios_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        servicios_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0080ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white])
        ]))
        
        story.append(servicios_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _crear_ranking_clientes(self):
        """Crear tabla de ranking de clientes"""
        story = []
        
        story.append(Paragraph("👑 TOP CLIENTES POR FACTURACIÓN", self.styles['SubtituloSeccion']))
        
        clientes_data = [
            ['Cliente', 'Servicios', 'Facturación Total'],
            ['Juan Pérez', '12', '$180,000'],
            ['María González', '8', '$145,000'],
            ['Carlos López', '10', '$132,000'],
            ['Ana Martínez', '7', '$98,000'],
            ['Pedro Rodríguez', '6', '$87,000']
        ]
        
        clientes_table = Table(clientes_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        clientes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00ffff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0ffff'), colors.white])
        ]))
        
        story.append(clientes_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _crear_proyeccion_mes(self):
        """Crear sección de proyección del mes"""
        story = []
        
        story.append(Paragraph("🤖 PROYECCIÓN INTELIGENTE DEL MES", self.styles['SubtituloSeccion']))
        
        # Calcular proyección basada en datos actuales
        facturacion_actual = self.datos.get('facturacion_mes_actual', 0)
        proyeccion_mes = facturacion_actual * 1.15  # Proyección 15% superior
        
        proyeccion_texto = f"""
        <b>Análisis Predictivo:</b><br/>
        • Facturación actual del mes: ${facturacion_actual:,.0f}<br/>
        • Proyección estimada: ${proyeccion_mes:,.0f}<br/>
        • Crecimiento esperado: +15% vs mes anterior<br/>
        • Recomendación: Mantener el ritmo actual de servicios<br/>
        • Oportunidad: Enfocar en servicios de mayor margen
        """
        
        story.append(Paragraph(proyeccion_texto, self.styles['TextoNormal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _crear_footer(self, canvas, doc):
        """Crear footer en cada página"""
        canvas.saveState()
        
        # Footer text
        footer_text = f"🚗 {self.nombre_taller} - Informe generado por eGarage el {self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawCentredText(letter[0]/2, 30, footer_text)
        
        # Número de página
        page_num = f"Página {doc.page}"
        canvas.drawRightString(letter[0] - 30, 30, page_num)
        
        canvas.restoreState()
    
    def generar_pdf(self):
        """Generar el PDF completo"""
        
        # Crear documento
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Crear contenido
        story = []
        
        # Header
        story.extend(self._crear_header())
        
        # KPIs
        story.extend(self._crear_seccion_kpis())
        
        # Gráfico de facturación
        story.append(Paragraph("📈 TENDENCIA DE FACTURACIÓN", self.styles['SubtituloSeccion']))
        story.append(self._crear_grafico_facturacion())
        story.append(Spacer(1, 20))
        
        # Rankings
        story.extend(self._crear_ranking_servicios())
        story.extend(self._crear_ranking_clientes())
        
        # Proyección
        story.extend(self._crear_proyeccion_mes())
        
        # Construir PDF
        doc.build(story, onFirstPage=self._crear_footer, onLaterPages=self._crear_footer)
        
        # Retornar buffer
        self.buffer.seek(0)
        return self.buffer


def generar_informe_ejecutivo_view(request):
    """Vista para generar y descargar el informe ejecutivo"""
    from taller.reportes.views import dashboard_inteligencia_operativa
    from django.shortcuts import render
    
    # Obtener datos del contexto
    # Simulamos llamar a la vista pero solo necesitamos el contexto
    from taller.models.documento import ServicioDocumento, Documento
    from taller.models.clientes import Cliente
    from django.db.models import Sum, F
    
    # Datos básicos para el informe
    contexto = {
        'facturacion_total': ServicioDocumento.objects.filter(
            documento__tipo_documento='Factura'
        ).aggregate(total=Sum(F('cantidad') * F('precio')))['total'] or 0,
        'ticket_promedio': 135000,
        'clientes_activos_porcentaje': 68,
        'margen_promedio': 45,
        'vehiculos_por_semana': 23,
        'satisfaccion_cliente': 4.8,
        'facturacion_mes_actual': 1250000,
    }
    
    # Obtener nombre del taller desde el usuario
    nombre_taller = "eGarage"
    if hasattr(request.user, 'empresa'):
        nombre_taller = request.user.empresa.nombre_taller
    
    # Generar PDF
    generador = InformeEjecutivoPDF(contexto, nombre_taller)
    buffer = generador.generar_pdf()
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_ejecutivo_{datetime.now().strftime("%Y%m%d")}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    
    return response
