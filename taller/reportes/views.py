from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from taller.models.documento import ServicioDocumento, Documento
from taller.models.vehiculos import Vehiculo
from taller.models.modelo import Modelo
from taller.models.marca import Marca
from taller.models.clientes import Cliente
from taller.models.mecanico import Mecanico
from taller.utils.motor_ia import MotorDiagnosticoIA
from collections import defaultdict
from datetime import timedelta, date, datetime
from django.db.models import Sum, Count, F, Q, Avg, FloatField, ExpressionWrapper
from django.utils import timezone
import json
import calendar

def reportes_dashboard(request):
    return render(request, 'taller/reportes/reportes.html')

def reporte_repuestos(request):
    from django.db.models import Sum, F, FloatField, ExpressionWrapper
    from taller.models.documento import RepuestoDocumento
    from taller.models.repuesto import Repuesto
    from collections import defaultdict
    
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    # Top 10 repuestos más vendidos - FILTRADO POR EMPRESA
    repuesto_ventas = (
        RepuestoDocumento.objects.filter(
            documento__tipo_documento='Factura',
            documento__empresa=empresa  # 🔒 FILTRO EMPRESA
        )
        .values('codigo', 'nombre')
        .annotate(cantidad_total=Sum('cantidad'), ingresos=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField())))
        .order_by('-cantidad_total')
    )
    top_repuestos = list(repuesto_ventas[:10])

    # Repuestos con mayor margen de ganancia - FILTRADO POR EMPRESA
    top_margen = []
    from django.db.models import Q
    for r in Repuesto.objects.filter(empresa=empresa):  # 🔒 FILTRO EMPRESA
        vendidos = RepuestoDocumento.objects.filter(
            codigo=r.part_number, 
            documento__tipo_documento='Factura',
            documento__empresa=empresa  # 🔒 FILTRO EMPRESA
        )
        total = vendidos.aggregate(total=Sum('cantidad'))['total'] or 0
        ingresos = vendidos.aggregate(ingresos=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField())))['ingresos'] or 0
        if total > 0 and r.precio_compra and r.precio_compra > 0:
            margen = float(r.precio_venta - r.precio_compra) / float(r.precio_compra) * 100
            top_margen.append({
                'codigo': r.part_number,
                'nombre': r.nombre_repuesto,
                'margen': margen,
                'ingresos': ingresos
            })
    top_margen = sorted(top_margen, key=lambda x: x['margen'], reverse=True)[:10]

    # Repuestos con bajo stock - FILTRADO POR EMPRESA
    bajo_stock = Repuesto.objects.filter(
        stock__lte=5, 
        empresa=empresa  # 🔒 FILTRO EMPRESA
    ).values('part_number', 'nombre_repuesto', 'stock')
    bajo_stock = [{'codigo': r['part_number'], 'nombre': r['nombre_repuesto'], 'stock': r['stock']} for r in bajo_stock]

    # Histórico de ventas mensuales - FILTRADO POR EMPRESA
    ventas = (
        RepuestoDocumento.objects.filter(
            documento__tipo_documento='Factura',
            documento__empresa=empresa  # 🔒 FILTRO EMPRESA
        )
        .annotate(mes=F('documento__fecha'))
        .values('mes')
        .annotate(total=Sum('cantidad'))
        .order_by('mes')
    )
    ventas_mensuales = defaultdict(int)
    for v in ventas:
        mes = v['mes'].strftime('%Y-%m') if v['mes'] else 'Sin fecha'
        ventas_mensuales[mes] += v['total']
    labels = list(ventas_mensuales.keys())
    data = list(ventas_mensuales.values())

    # Repuestos nunca vendidos - FILTRADO POR EMPRESA
    vendidos_codigos = set(RepuestoDocumento.objects.filter(
        documento__tipo_documento='Factura',
        documento__empresa=empresa  # 🔒 FILTRO EMPRESA
    ).values_list('codigo', flat=True))
    nunca_vendidos = Repuesto.objects.filter(empresa=empresa).exclude(part_number__in=vendidos_codigos)  # 🔒 FILTRO EMPRESA
    nunca_vendidos = [{'codigo': r.part_number, 'nombre': r.nombre_repuesto} for r in nunca_vendidos]

    context = {
        'top_repuestos': top_repuestos,
        'top_margen': top_margen,
        'bajo_stock': bajo_stock,
        'ventas_mensuales': {'labels': labels, 'data': data},
        'nunca_vendidos': nunca_vendidos,
    }
    return render(request, 'taller/reportes/reporte_repuestos.html', context)

def reporte_servicios(request):
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    # Panel de facturación - FILTRADO POR EMPRESA
    # Total
    facturacion_total = ServicioDocumento.objects.filter(
        documento__empresa=empresa  # 🔒 FILTRO EMPRESA
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    # Por periodo (últimos 6 meses) - FILTRADO POR EMPRESA
    from datetime import date, timedelta
    hoy = date.today()
    hace_6_meses = hoy - timedelta(days=180)
    facturacion_periodo_qs = (
        ServicioDocumento.objects
        .filter(
            documento__fecha__gte=hace_6_meses,
            documento__empresa=empresa  # 🔒 FILTRO EMPRESA
        )
        .annotate(mes=F('documento__fecha'))
        .values('mes')
        .annotate(total=Sum('precio'))
        .order_by('mes')
    )
    facturacion_periodo = [
        {'mes': f['mes'].strftime('%Y-%m') if f['mes'] else 'Sin fecha', 'total': f['total']} for f in facturacion_periodo_qs
    ]
    
    # Por servicio - FILTRADO POR EMPRESA
    facturacion_servicio = list(
        ServicioDocumento.objects
        .filter(documento__empresa=empresa)  # 🔒 FILTRO EMPRESA
        .values('nombre')
        .annotate(total=Sum('precio'))
        .order_by('-total')[:10]
    )
    for f in facturacion_servicio:
        f['nombre'] = f['nombre'] or 'Sin nombre'
        
    # Por cliente - FILTRADO POR EMPRESA
    facturacion_cliente_qs = (
        ServicioDocumento.objects
        .filter(documento__empresa=empresa)  # 🔒 FILTRO EMPRESA
        .values('documento__cliente__nombre', 'documento__cliente__apellido')
        .annotate(total=Sum('precio'))
        .order_by('-total')[:10]
    )
    facturacion_cliente = [
        {'cliente': (f['documento__cliente__nombre'] or '') + (' ' + f['documento__cliente__apellido'] if f['documento__cliente__apellido'] else ''), 'total': f['total']} for f in facturacion_cliente_qs
    ]
    
    Servicio = None
    try:
        from taller.servicios.models import Servicio
    except ImportError:
        pass

    # Top 10 servicios más vendidos - FILTRADO POR EMPRESA
    top_servicios = (
        ServicioDocumento.objects
        .filter(documento__empresa=empresa)  # 🔒 FILTRO EMPRESA
        .values('nombre')
        .annotate(cantidad=Count('id'), total=Sum('precio'))
        .order_by('-cantidad')[:10]
    )

    # Servicios con mayor facturación - FILTRADO POR EMPRESA
    top_facturacion = (
        ServicioDocumento.objects
        .filter(documento__empresa=empresa)  # 🔒 FILTRO EMPRESA
        .values('nombre')
        .annotate(total=Sum('precio'), cantidad=Count('id'))
        .order_by('-total')[:10]
    )

    # Histórico de servicios mensuales - FILTRADO POR EMPRESA
    servicios_mes = (
        ServicioDocumento.objects
        .filter(documento__empresa=empresa)  # 🔒 FILTRO EMPRESA
        .annotate(mes=F('documento__fecha'))
        .values('mes')
        .annotate(total=Sum('precio'))
        .order_by('mes')
    )
    historico = defaultdict(int)
    for s in servicios_mes:
        mes = s['mes'].strftime('%Y-%m') if s['mes'] else 'Sin fecha'
        historico[mes] += s['total']
    labels = list(historico.keys())
    data = list(historico.values())

    # Servicios nunca vendidos (si existe catálogo de servicios)
    nunca_vendidos = []
    if Servicio:
        vendidos_nombres = set(ServicioDocumento.objects.values_list('nombre', flat=True))
        nunca_vendidos = Servicio.objects.exclude(nombre__in=vendidos_nombres)
        nunca_vendidos = [{'nombre': s.nombre} for s in nunca_vendidos]

    # Rankings de vehículos atendidos
    from taller.models.vehiculos import Vehiculo
    from taller.models.modelo import Modelo
    from taller.models.marca import Marca
    from taller.models.clientes import Cliente
    from taller.models.documento import Documento
    # Solo documentos con servicios realizados
    doc_ids = ServicioDocumento.objects.values_list('documento_id', flat=True)
    vehiculos = Vehiculo.objects.filter(documento__id__in=doc_ids).distinct()
    # Ranking de modelos
    ranking_modelos = (
        vehiculos.values('modelo__nombre')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:10]
    )
    ranking_modelos = [
        {'modelo': r['modelo__nombre'] or 'Sin modelo', 'cantidad': r['cantidad']} for r in ranking_modelos
    ]
    # Ranking de marcas
    ranking_marcas = (
        vehiculos.values('marca__nombre')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:10]
    )
    ranking_marcas = [
        {'marca': r['marca__nombre'] or 'Sin marca', 'cantidad': r['cantidad']} for r in ranking_marcas
    ]
    # Ranking de años
    ranking_anios = (
        vehiculos.values('anio')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:10]
    )
    ranking_anios = [
        {'anio': r['anio'] or 'Sin año', 'cantidad': r['cantidad']} for r in ranking_anios
    ]
    # Ranking de clientes frecuentes
    ranking_clientes = (
        vehiculos.values('cliente__nombre', 'cliente__apellido')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:10]
    )
    ranking_clientes = [
        {'cliente': (r['cliente__nombre'] or '') + (' ' + r['cliente__apellido'] if r['cliente__apellido'] else ''), 'cantidad': r['cantidad']} for r in ranking_clientes
    ]

    # Panel de clientes
    from datetime import timedelta, date
    hoy = date.today()
    hace_3_meses = hoy - timedelta(days=90)
    # Clientes activos: con más documentos en los últimos 6 meses
    clientes_activos = list(
        Cliente.objects
        .filter(documento__fecha__gte=hoy - timedelta(days=180))
        .annotate(cantidad=Count('documento'))
        .order_by('-cantidad')
        .values('nombre', 'apellido', 'cantidad')[:10]
    )
    for c in clientes_activos:
        c['nombre'] = (c['nombre'] or '') + (' ' + c['apellido'] if c['apellido'] else '')
    # Clientes nuevos: creados en los últimos 3 meses
    clientes_nuevos = list(
        Cliente.objects
        .filter(documento__fecha__gte=hace_3_meses)
        .annotate(fecha_alta=F('documento__fecha'))
        .order_by('-fecha_alta')
        .values('nombre', 'apellido', 'fecha_alta')
        .distinct()[:10]
    )
    for c in clientes_nuevos:
        c['nombre'] = (c['nombre'] or '') + (' ' + c['apellido'] if c['apellido'] else '')
    # Clientes históricos: con más documentos en total
    clientes_historicos = list(
        Cliente.objects
        .annotate(cantidad=Count('documento'))
        .order_by('-cantidad')
        .values('nombre', 'apellido', 'cantidad')[:10]
    )
    for c in clientes_historicos:
        c['nombre'] = (c['nombre'] or '') + (' ' + c['apellido'] if c['apellido'] else '')
    # Clientes recurrentes: más de 1 documento en el último año
    clientes_recurrentes = list(
        Cliente.objects
        .filter(documento__fecha__gte=hoy - timedelta(days=365))
        .annotate(cantidad=Count('documento'))
        .filter(cantidad__gt=1)
        .order_by('-cantidad')
        .values('nombre', 'apellido', 'cantidad')[:10]
    )
    for c in clientes_recurrentes:
        c['nombre'] = (c['nombre'] or '') + (' ' + c['apellido'] if c['apellido'] else '')

    # Agenda y turnos: próximos turnos (documentos con fecha futura)
    turnos_proximos = list(
        Documento.objects
        .filter(fecha__gte=hoy)
        .order_by('fecha')
        .values('fecha', 'cliente__nombre', 'cliente__apellido', 'vehiculo__patente', 'vehiculo__marca__nombre', 'vehiculo__modelo__nombre', 'tipo_documento')[:20]
    )
    for t in turnos_proximos:
        t['cliente'] = (t['cliente__nombre'] or '') + (' ' + t['cliente__apellido'] if t['cliente__apellido'] else '')
        t['vehiculo'] = (t['vehiculo__marca__nombre'] or '') + ' ' + (t['vehiculo__modelo__nombre'] or '') + ' (' + (t['vehiculo__patente'] or '-') + ')'
    context = {
        'top_servicios': top_servicios,
        'top_facturacion': top_facturacion,
        'historico_servicios': {'labels': labels, 'data': data},
        'nunca_vendidos': nunca_vendidos,
        'ranking_modelos': ranking_modelos,
        'ranking_marcas': ranking_marcas,
        'ranking_anios': ranking_anios,
        'ranking_clientes': ranking_clientes,
        'clientes_activos': clientes_activos,
        'clientes_nuevos': clientes_nuevos,
        'clientes_historicos': clientes_historicos,
        'clientes_recurrentes': clientes_recurrentes,
        'facturacion_total': facturacion_total,
        'facturacion_periodo': facturacion_periodo,
        'facturacion_servicio': facturacion_servicio,
        'facturacion_cliente': facturacion_cliente,
        'turnos_proximos': turnos_proximos,
    }
    return render(request, 'taller/reportes/reporte_servicios.html', context)


def dashboard_inteligencia_operativa(request):
    """
    🚀 Centro de Inteligencia Operativa - Dashboard Futurista 360°
    Análisis predictivo y KPIs avanzados para talleres automotrices
    """
    from django.db.models import Sum, Count, F, Avg, Q
    from decimal import Decimal
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # � FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    # �📊 Calcular KPIs principales - FILTRADO POR EMPRESA
    facturacion_total = ServicioDocumento.objects.filter(
        documento__tipo_documento='Factura',
        documento__empresa=empresa  # 🔒 FILTRO EMPRESA
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    # Calcular métricas adicionales para KPIs - FILTRADO POR EMPRESA
    total_documentos = Documento.objects.filter(
        tipo_documento='Factura',
        empresa=empresa  # 🔒 FILTRO EMPRESA
    ).count()
    total_clientes = Cliente.objects.filter(empresa=empresa).count()  # 🔒 FILTRO EMPRESA
    total_vehiculos = Vehiculo.objects.filter(empresa=empresa).count()  # 🔒 FILTRO EMPRESA
    
    # Facturación del mes actual vs mes anterior - FILTRADO POR EMPRESA
    hoy = timezone.now().date()
    inicio_mes_actual = hoy.replace(day=1)
    if inicio_mes_actual.month == 1:
        inicio_mes_anterior = inicio_mes_actual.replace(year=inicio_mes_actual.year - 1, month=12)
    else:
        inicio_mes_anterior = inicio_mes_actual.replace(month=inicio_mes_actual.month - 1)
    
    facturacion_mes_actual = ServicioDocumento.objects.filter(
        documento__tipo_documento='Factura',
        documento__fecha__gte=inicio_mes_actual,
        documento__empresa=empresa  # 🔒 FILTRO EMPRESA
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    facturacion_mes_anterior = ServicioDocumento.objects.filter(
        documento__tipo_documento='Factura',
        documento__fecha__gte=inicio_mes_anterior,
        documento__fecha__lt=inicio_mes_actual,
        documento__empresa=empresa  # 🔒 FILTRO EMPRESA
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    # Calcular datos para gráficos de facturación mensual - FILTRADO POR EMPRESA
    facturacion_por_mes = []
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for i in range(6):  # Últimos 6 meses
        fecha_mes = hoy.replace(day=1) - timedelta(days=30 * (5-i))
        inicio_mes = fecha_mes.replace(day=1)
        if inicio_mes.month == 12:
            fin_mes = inicio_mes.replace(year=inicio_mes.year + 1, month=1)
        else:
            fin_mes = inicio_mes.replace(month=inicio_mes.month + 1)
        
        facturacion = ServicioDocumento.objects.filter(
            documento__tipo_documento='Factura',
            documento__fecha__gte=inicio_mes,
            documento__fecha__lt=fin_mes,
            documento__empresa=empresa  # 🔒 FILTRO EMPRESA
        ).aggregate(total=Sum('precio'))['total'] or 0
        
        facturacion_por_mes.append({
            'mes': meses[inicio_mes.month - 1],
            'valor': float(facturacion)
        })
    
    # Datos para gráfico de servicios más demandados - FILTRADO POR EMPRESA
    servicios_demandados = ServicioDocumento.objects.filter(
        documento__tipo_documento='Factura',
        documento__empresa=empresa  # 🔒 FILTRO EMPRESA
    ).values('nombre').annotate(
        total_servicios=Count('id'),
        total_ingresos=Sum('precio')
    ).order_by('-total_servicios')[:5]
    
    # Datos para mapa térmico (servicios por día de la semana) - FILTRADO POR EMPRESA
    servicios_por_dia = []
    for i in range(28):  # Últimas 4 semanas
        fecha = hoy - timedelta(days=i)
        servicios_dia = Documento.objects.filter(
            tipo_documento='Factura',
            fecha=fecha,
            empresa=empresa  # 🔒 FILTRO EMPRESA
        ).count()
        servicios_por_dia.append({
            'fecha': fecha,
            'servicios': servicios_dia,
            'dia_semana': fecha.weekday()  # 0=Lunes, 6=Domingo
        })
    
    # Clientes que no han vuelto en 60 días - FILTRADO POR EMPRESA
    hace_60_dias = hoy - timedelta(days=60)
    clientes_inactivos = Cliente.objects.filter(
        documento__fecha__lt=hace_60_dias,
        empresa=empresa  # 🔒 FILTRO EMPRESA
    ).distinct().count()
    
    context = {
        'facturacion_total': facturacion_total,
        'total_documentos': total_documentos,
        'total_clientes': total_clientes,
        'total_vehiculos': total_vehiculos,
        'facturacion_mes_actual': facturacion_mes_actual,
        'facturacion_mes_anterior': facturacion_mes_anterior,
        'facturacion_por_mes': facturacion_por_mes,
        'servicios_demandados': list(servicios_demandados),
        'servicios_por_dia': servicios_por_dia,
        'clientes_inactivos': clientes_inactivos,
        # KPIs calculados
        'ticket_promedio': facturacion_total / max(total_documentos, 1),
        'clientes_activos_porcentaje': 68,  # Simulado por ahora
        'margen_promedio': 45,  # Simulado por ahora
        'ingresos_por_hora': 22500,  # Simulado por ahora
        'vehiculos_por_semana': 23,  # Simulado por ahora
        'satisfaccion_cliente': 4.8,  # Simulado por ahora
    }
    
    return render(request, 'taller/reportes/dashboard_inteligencia_operativa.html', context)


def diagnostico_ia(request):
    """
    🧠 Diagnóstico por IA - Análisis Predictivo Avanzado
    Motor de inteligencia artificial para optimización de talleres automotrices
    """
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    # Obtener documentos para análisis - FILTRADO POR EMPRESA
    documentos = Documento.objects.select_related('cliente', 'vehiculo').prefetch_related('serviciosdocumento_set').filter(
        empresa=empresa  # 🔒 FILTRO EMPRESA
    ).all()
    
    # Inicializar motor de IA
    motor_ia = MotorDiagnosticoIA()
    
    # Realizar análisis completo
    resultados = motor_ia.analizar_servicios_completo(documentos)
    
    # Preparar contexto para template
    contexto = {
        'servicios_crecimiento': resultados['servicios_crecimiento'],
        'servicios_declive': resultados['servicios_declive'],
        'estacionalidad': resultados['estacionalidad'],
        'comparativa_mercado': resultados['comparativa_mercado'],
        'recomendaciones_ia': resultados['recomendaciones_ia'],
        'predicciones_ingresos': resultados['predicciones_ingresos'],
        'alertas_criticas': resultados['alertas_criticas'],
        'insights_ai': resultados['insights_ai'],
        'total_documentos': documentos.count(),
        'fecha_analisis': date.today().strftime('%d/%m/%Y')
    }

# ==================== REPORTES POR MECÁNICO ====================

def reportes_mecanicos(request):
    """Vista principal para reportes por mecánico con IA"""
    
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    # Obtener filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    mecanico_id = request.GET.get('mecanico_id')
    
    # Valores por defecto
    if not fecha_desde:
        fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = date.today().strftime('%Y-%m-%d')
    
    # Filtrar documentos base - FILTRADO POR EMPRESA
    documentos_qs = Documento.objects.filter(
        fecha__range=[fecha_desde, fecha_hasta],
        mecanico__isnull=False,
        empresa=empresa  # 🔒 FILTRO EMPRESA
    )
    
    if mecanico_id and mecanico_id != 'todos':
        documentos_qs = documentos_qs.filter(mecanico_id=mecanico_id)
    
    # Métricas generales - YA FILTRADO POR EMPRESA
    total_documentos = documentos_qs.count()
    total_generado = documentos_qs.aggregate(
        total=Sum('servicios__precio')
    )['total'] or 0
    
    promedio_por_documento = round(
        total_generado / total_documentos if total_documentos > 0 else 0, 0
    )
    
    # Servicios más frecuentes - YA FILTRADO POR EMPRESA
    servicios_frecuentes = (
        ServicioDocumento.objects
        .filter(documento__in=documentos_qs)
        .values('nombre')
        .annotate(cantidad=Count('id'), total_ingresos=Sum('precio'))
        .order_by('-cantidad')[:5]
    )
    
    # Datos por mecánico - FILTRADO POR EMPRESA
    mecanicos_data = []
    for mecanico in Mecanico.objects.filter(empresa=empresa):  # 🔒 FILTRO EMPRESA
        docs_mecanico = documentos_qs.filter(mecanico=mecanico)
        servicios_mecanico = ServicioDocumento.objects.filter(documento__in=docs_mecanico)
        
        total_docs = docs_mecanico.count()
        total_servicios = servicios_mecanico.count()
        total_generado_mec = servicios_mecanico.aggregate(Sum('precio'))['precio__sum'] or 0
        promedio_doc = round(total_generado_mec / total_docs if total_docs > 0 else 0, 0)
        
        # Servicios más realizados por este mecánico
        servicios_top = (
            servicios_mecanico
            .values('nombre')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')[:3]
        )
        
        mecanicos_data.append({
            'mecanico': mecanico,
            'total_documentos': total_docs,
            'total_servicios': total_servicios,
            'total_generado': total_generado_mec,
            'promedio_por_documento': promedio_doc,
            'servicios_top': list(servicios_top)
        })
    
    # Ordenar por total generado
    mecanicos_data.sort(key=lambda x: x['total_generado'], reverse=True)
    
    # ==================== INTELIGENCIA ARTIFICIAL ====================
    ia_insights = generar_insights_ia_mecanicos(mecanicos_data, fecha_desde, fecha_hasta)
    
    # Todos los mecánicos para el filtro - FILTRADO POR EMPRESA
    todos_mecanicos = Mecanico.objects.filter(empresa=empresa).order_by('nombre')
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'mecanico_seleccionado': mecanico_id,
        'todos_mecanicos': todos_mecanicos,
        'total_documentos': total_documentos,
        'total_generado': total_generado,
        'promedio_por_documento': promedio_por_documento,
        'servicios_frecuentes': servicios_frecuentes,
        'mecanicos_data': mecanicos_data,
        'ia_insights': ia_insights,
    }
    
    return render(request, 'taller/reportes/reportes_mecanicos.html', context)


def generar_insights_ia_mecanicos(mecanicos_data, fecha_desde, fecha_hasta):
    """Genera insights de IA para reportes de mecánicos"""
    
    insights = {
        'predicciones': [],
        'alertas': [],
        'sugerencias': [],
        'comparativas': []
    }
    
    if not mecanicos_data:
        return insights
    
    # Calcular días del periodo
    fecha_inicio = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    
    # 🧠 PREDICCIONES
    for data in mecanicos_data[:3]:  # Top 3 mecánicos
        if data['total_documentos'] > 0 and dias_periodo > 0:
            docs_por_dia = data['total_documentos'] / dias_periodo
            ingresos_por_dia = data['total_generado'] / dias_periodo
            
            # Proyección mensual
            proyeccion_mensual = round(ingresos_por_dia * 30, 0)
            insights['predicciones'].append({
                'mecanico': data['mecanico'].nombre,
                'proyeccion_mensual': proyeccion_mensual,
                'docs_proyectados': round(docs_por_dia * 30, 0)
            })
    
    # 🚨 ALERTAS
    if len(mecanicos_data) >= 2:
        mejor_mecanico = mecanicos_data[0]
        peor_mecanico = mecanicos_data[-1]
        
        if mejor_mecanico['total_generado'] > 0 and peor_mecanico['total_generado'] > 0:
            diferencia_porcentual = round(
                ((mejor_mecanico['total_generado'] - peor_mecanico['total_generado']) / 
                 mejor_mecanico['total_generado']) * 100, 1
            )
            
            if diferencia_porcentual > 50:
                insights['alertas'].append({
                    'tipo': 'rendimiento',
                    'mensaje': f"Gran diferencia de rendimiento: {mejor_mecanico['mecanico'].nombre} supera a {peor_mecanico['mecanico'].nombre} por {diferencia_porcentual}%"
                })
    
    # Alertas de baja productividad
    promedio_general = sum(d['total_generado'] for d in mecanicos_data) / len(mecanicos_data)
    for data in mecanicos_data:
        if data['total_generado'] < promedio_general * 0.6:  # 60% del promedio
            insights['alertas'].append({
                'tipo': 'productividad',
                'mensaje': f"{data['mecanico'].nombre} está 40% por debajo del promedio del equipo"
            })
    
    # 💡 SUGERENCIAS
    # Mecánico más eficiente en servicios específicos
    servicios_por_mecanico = {}
    for data in mecanicos_data:
        for servicio in data['servicios_top']:
            servicio_nombre = servicio['nombre']
            if servicio_nombre not in servicios_por_mecanico:
                servicios_por_mecanico[servicio_nombre] = []
            servicios_por_mecanico[servicio_nombre].append({
                'mecanico': data['mecanico'].nombre,
                'cantidad': servicio['cantidad']
            })
    
    for servicio, mecans in servicios_por_mecanico.items():
        if len(mecans) > 1:
            mejor_en_servicio = max(mecans, key=lambda x: x['cantidad'])
            insights['sugerencias'].append({
                'tipo': 'especialización',
                'mensaje': f"'{servicio}': {mejor_en_servicio['mecanico']} es el más especializado ({mejor_en_servicio['cantidad']} realizados)"
            })
    
    # 📊 COMPARATIVAS
    if len(mecanicos_data) >= 2:
        # Encontrar el mecánico con mejor promedio por documento
        mejor_promedio = max(mecanicos_data, key=lambda x: x['promedio_por_documento'])
        insights['comparativas'].append({
            'tipo': 'eficiencia',
            'mensaje': f"{mejor_promedio['mecanico'].nombre} tiene el mejor promedio por documento: ${mejor_promedio['promedio_por_documento']:,.0f}"
        })
        
        # Mecánico más activo (más documentos)
        mas_activo = max(mecanicos_data, key=lambda x: x['total_documentos'])
        insights['comparativas'].append({
            'tipo': 'actividad',
            'mensaje': f"{mas_activo['mecanico'].nombre} es el más activo con {mas_activo['total_documentos']} documentos"
        })
    
    return insights


def exportar_mecanicos_excel(request):
    """Exporta reporte de mecánicos a Excel"""
    try:
        import pandas as pd
        import io
        
        # 🔒 FILTRO CRÍTICO POR EMPRESA
        try:
            empresa = request.user.empresa
        except AttributeError:
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                nombre_taller="Taller Demo",
                defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
            )
        
        # Obtener los mismos filtros que la vista principal
        fecha_desde = request.GET.get('fecha_desde', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        fecha_hasta = request.GET.get('fecha_hasta', date.today().strftime('%Y-%m-%d'))
        mecanico_id = request.GET.get('mecanico_id')
        
        # Filtrar documentos - FILTRADO POR EMPRESA
        documentos_qs = Documento.objects.filter(
            fecha__range=[fecha_desde, fecha_hasta],
            mecanico__isnull=False,
            empresa=empresa  # 🔒 FILTRO EMPRESA
        )
        
        if mecanico_id and mecanico_id != 'todos':
            documentos_qs = documentos_qs.filter(mecanico_id=mecanico_id)
        
        # Preparar datos
        data = []
        for documento in documentos_qs:
            servicios = ServicioDocumento.objects.filter(documento=documento)
            total_servicios = servicios.aggregate(Sum('precio'))['precio__sum'] or 0
            
            data.append({
                'Fecha': documento.fecha,
                'Mecánico': documento.mecanico.nombre if documento.mecanico else 'Sin asignar',
                'Tipo Documento': documento.tipo_documento,
                'Número': documento.numero_documento,
                'Cliente': str(documento.cliente) if documento.cliente else '',
                'Vehículo': f"{documento.vehiculo.patente} - {documento.vehiculo.modelo}" if documento.vehiculo else '',
                'Cantidad Servicios': servicios.count(),
                'Total Generado': total_servicios,
            })
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reporte Mecánicos', index=False)
            
            # Agregar hoja de resumen - FILTRADO POR EMPRESA
            resumen_data = []
            for mecanico in Mecanico.objects.filter(empresa=empresa):  # 🔒 FILTRO EMPRESA
                docs_mecanico = documentos_qs.filter(mecanico=mecanico)
                servicios_mecanico = ServicioDocumento.objects.filter(documento__in=docs_mecanico)
                total_generado = servicios_mecanico.aggregate(Sum('precio'))['precio__sum'] or 0
                
                resumen_data.append({
                    'Mecánico': mecanico.nombre,
                    'Total Documentos': docs_mecanico.count(),
                    'Total Servicios': servicios_mecanico.count(),
                    'Total Generado': total_generado,
                    'Promedio por Documento': round(total_generado / docs_mecanico.count() if docs_mecanico.count() > 0 else 0, 0)
                })
            
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen por Mecánico', index=False)
        
        output.seek(0)
        
        # Respuesta HTTP
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_mecanicos_{fecha_desde}_{fecha_hasta}.xlsx"'
        
        return response
    
    except ImportError:
        # Si pandas no está disponible, generar CSV simple
        import csv
        
        fecha_desde = request.GET.get('fecha_desde', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        fecha_hasta = request.GET.get('fecha_hasta', date.today().strftime('%Y-%m-%d'))
        
        documentos_qs = Documento.objects.filter(
            fecha__range=[fecha_desde, fecha_hasta],
            mecanico__isnull=False
        )
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_mecanicos_{fecha_desde}_{fecha_hasta}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Mecánico', 'Tipo Documento', 'Número', 'Cliente', 'Total Generado'])
        
        for documento in documentos_qs:
            servicios = ServicioDocumento.objects.filter(documento=documento)
            total_servicios = servicios.aggregate(Sum('precio'))['precio__sum'] or 0
            
            writer.writerow([
                documento.fecha,
                documento.mecanico.nombre if documento.mecanico else 'Sin asignar',
                documento.tipo_documento,
                documento.numero_documento,
                str(documento.cliente) if documento.cliente else '',
                total_servicios
            ])
        
        return response


def generar_resumen_whatsapp_mecanico(request, mecanico_id):
    """Genera resumen para enviar por WhatsApp a un mecánico específico"""
    from datetime import date, timedelta
    
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    try:
        mecanico = Mecanico.objects.get(id=mecanico_id, empresa=empresa)  # 🔒 FILTRO EMPRESA
    except Mecanico.DoesNotExist:
        return JsonResponse({'error': 'Mecánico no encontrado'}, status=404)
    
    # Últimos 7 días
    fecha_desde = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
    fecha_hasta = date.today().strftime('%Y-%m-%d')
    
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
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:3]
    )
    
    # Generar mensaje
    mensaje = f"""🔧 *RESUMEN SEMANAL - {mecanico.nombre.upper()}*
    
📅 *Período:* {fecha_desde} a {fecha_hasta}

📊 *MÉTRICAS:*
• Documentos procesados: {documentos.count()}
• Servicios realizados: {servicios.count()}
• Total generado: ${total_generado:,.0f}
• Promedio por documento: ${(total_generado / documentos.count() if documentos.count() > 0 else 0):,.0f}

🏆 *TUS SERVICIOS TOP:*"""
    
    for i, servicio in enumerate(servicios_top, 1):
        mensaje += f"\n{i}. {servicio['nombre']} ({servicio['cantidad']} veces)"
    
    mensaje += f"\n\n💪 ¡Excelente trabajo!\n_Generado por eGarage IA_"
    
    return JsonResponse({
        'mensaje': mensaje,
        'mecanico': mecanico.nombre,
        'telefono': getattr(mecanico, 'telefono', ''),  # Si tienes campo teléfono
        'whatsapp_url': f"https://wa.me/?text={mensaje.replace(' ', '%20').replace('\n', '%0A')}"
    })


def api_mecanicos_chart_data(request):
    """API para datos de gráficos de mecánicos"""
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    fecha_desde = request.GET.get('fecha_desde', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('fecha_hasta', date.today().strftime('%Y-%m-%d'))
    
    # Filtrar documentos - FILTRADO POR EMPRESA
    documentos_qs = Documento.objects.filter(
        fecha__range=[fecha_desde, fecha_hasta],
        mecanico__isnull=False,
        empresa=empresa  # 🔒 FILTRO EMPRESA
    )
    
    # Datos por mecánico para gráfico de barras - FILTRADO POR EMPRESA
    mecanicos_chart = []
    for mecanico in Mecanico.objects.filter(empresa=empresa):  # 🔒 FILTRO EMPRESA
        docs_mecanico = documentos_qs.filter(mecanico=mecanico)
        servicios_mecanico = ServicioDocumento.objects.filter(documento__in=docs_mecanico)
        total_generado = servicios_mecanico.aggregate(Sum('precio'))['precio__sum'] or 0
        
        if total_generado > 0:  # Solo incluir mecánicos con actividad
            mecanicos_chart.append({
                'nombre': mecanico.nombre,
                'total': float(total_generado),
                'documentos': docs_mecanico.count()
            })
    
    # Datos de evolución temporal (últimos 7 días)
    evolucion_data = []
    for i in range(7):
        fecha = date.today() - timedelta(days=6-i)
        docs_dia = documentos_qs.filter(fecha=fecha)
        servicios_dia = ServicioDocumento.objects.filter(documento__in=docs_dia)
        total_dia = servicios_dia.aggregate(Sum('precio'))['precio__sum'] or 0
        
        evolucion_data.append({
            'fecha': fecha.strftime('%d/%m'),
            'total': float(total_dia),
            'documentos': docs_dia.count()
        })
    
    return JsonResponse({
        'mecanicos': mecanicos_chart,
        'evolucion': evolucion_data
    })


def generar_pdf_mecanico(request, mecanico_id):
    """Genera PDF individual para un mecánico"""
    from .exporters import generar_pdf_mecanico as pdf_generator
    
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            nombre_taller="Taller Demo",
            defaults={'direccion': 'Demo', 'telefono': '123456789', 'email': 'demo@ejemplo.com'}
        )
    
    try:
        fecha_desde = request.GET.get('fecha_desde', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        fecha_hasta = request.GET.get('fecha_hasta', date.today().strftime('%Y-%m-%d'))
        
        pdf_content = pdf_generator(mecanico_id, fecha_desde, fecha_hasta)
        
        if isinstance(pdf_content, bytes):
            # PDF generado correctamente - verificar que el mecánico pertenece a la empresa
            mecanico = Mecanico.objects.get(id=mecanico_id, empresa=empresa)  # 🔒 FILTRO EMPRESA
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{mecanico.nombre}_{fecha_desde}_{fecha_hasta}.pdf"'
            return response
        else:
            # Error o HTML fallback
            return HttpResponse(pdf_content, content_type='text/html')
    
    except Mecanico.DoesNotExist:
        return JsonResponse({'error': 'Mecánico no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error generando PDF: {str(e)}'}, status=500)
    
    return render(request, 'taller/reportes/diagnostico_ia.html', contexto)


# ===== NUEVAS VISTAS PARA REPORTES POR FECHA =====

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from collections import defaultdict
from decimal import Decimal

@login_required
def reportes_por_fecha(request):
    """Vista principal para reportes por fecha - punto de entrada unificado"""
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')
    tipo = request.GET.get('tipo')
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )

    # Si no hay fechas, mostrar formulario vacío
    if not (desde and hasta):
        return render(request, 'taller/reportes/reportes_por_fecha.html', {
            'empresa': empresa
        })

    # Filtrar documentos por empresa y fechas
    queryset = Documento.objects.filter(
        empresa=empresa,
        fecha__range=[desde, hasta]
    ).select_related('cliente', 'mecanico', 'vehiculo').order_by('-fecha')

    # Redireccionar según el tipo seleccionado
    if tipo == 'repuesto':
        return redirect('reportes:reportes_repuestos_fecha', desde=desde, hasta=hasta)
    elif tipo == 'servicio':
        return redirect('reportes:reportes_servicios_fecha', desde=desde, hasta=hasta)
    elif tipo == 'otros':
        return redirect('reportes:reportes_otros_servicios_fecha', desde=desde, hasta=hasta)

    # Filtrar por tipo de documento específico
    if tipo == 'factura':
        queryset = queryset.filter(tipo_documento='Factura')
    elif tipo == 'orden':
        queryset = queryset.filter(tipo_documento='Orden de trabajo')
    elif tipo == 'presupuesto':
        queryset = queryset.filter(tipo_documento='Presupuesto')

    # Calcular resumen por tipos
    resumen_tipos = {
        'facturas': {
            'nombre': 'Facturas',
            'count': queryset.filter(tipo_documento='Factura').count(),
            'icon': '💰'
        },
        'ordenes': {
            'nombre': 'Órdenes',
            'count': queryset.filter(tipo_documento='Orden de trabajo').count(),
            'icon': '🔧'
        },
        'presupuestos': {
            'nombre': 'Presupuestos',
            'count': queryset.filter(tipo_documento='Presupuesto').count(),
            'icon': '📋'
        }
    }

    # Calcular total general
    total_general = Decimal('0')
    for doc in queryset:
        try:
            if hasattr(doc, 'calcular_total'):
                total_general += doc.calcular_total() or Decimal('0')
        except:
            pass

    context = {
        'documentos': queryset,
        'resumen_tipos': resumen_tipos,
        'total_general': total_general,
        'desde': desde,
        'hasta': hasta,
        'tipo': tipo,
        'empresa': empresa
    }

    return render(request, 'taller/reportes/reportes_por_fecha.html', context)


@login_required
def reportes_repuestos_fecha(request, desde, hasta):
    """Vista específica para reportes de repuestos por fecha"""
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )

    from taller.models.documento import RepuestoDocumento
    
    # Filtrar repuestos por empresa y fechas
    repuestos = RepuestoDocumento.objects.filter(
        documento__empresa=empresa,
        documento__fecha__range=[desde, hasta]
    ).select_related('documento').order_by('-documento__fecha')

    # Calcular estadísticas
    total_repuestos = repuestos.aggregate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum('total')
    )

    # Top repuestos más vendidos
    top_repuestos = repuestos.values('nombre', 'part_number').annotate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum('total')
    ).order_by('-cantidad_total')[:10]

    context = {
        'repuestos': repuestos,
        'total_repuestos': total_repuestos,
        'top_repuestos': top_repuestos,
        'desde': desde,
        'hasta': hasta,
        'empresa': empresa
    }

    return render(request, 'taller/reportes/repuestos_fecha.html', context)


@login_required
def reportes_servicios_fecha(request, desde, hasta):
    """Vista específica para reportes de servicios por fecha"""
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )

    # Filtrar servicios por empresa y fechas
    servicios = ServicioDocumento.objects.filter(
        documento__empresa=empresa,
        documento__fecha__range=[desde, hasta]
    ).select_related('documento').order_by('-documento__fecha')

    # Calcular estadísticas
    total_servicios = servicios.aggregate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum('total')
    )

    # Top servicios más realizados
    top_servicios = servicios.values('nombre').annotate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum('total')
    ).order_by('-cantidad_total')[:10]

    context = {
        'servicios': servicios,
        'total_servicios': total_servicios,
        'top_servicios': top_servicios,
        'desde': desde,
        'hasta': hasta,
        'empresa': empresa
    }

    return render(request, 'taller/reportes/servicios_fecha.html', context)


@login_required
def reportes_otros_servicios_fecha(request, desde, hasta):
    """Vista específica para reportes de otros servicios por fecha"""
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )

    # Aquí puedes agregar la lógica para "otros servicios"
    # Por ejemplo, servicios externos, subcontratados, etc.
    
    # Por ahora, mostrar todos los servicios que no sean los principales
    servicios_externos = ServicioDocumento.objects.filter(
        documento__empresa=empresa,
        documento__fecha__range=[desde, hasta]
    ).exclude(
        nombre__icontains='cambio'
    ).exclude(
        nombre__icontains='reparacion'
    ).select_related('documento').order_by('-documento__fecha')

    # Calcular estadísticas
    total_otros = servicios_externos.aggregate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum('total')
    )

    context = {
        'servicios_externos': servicios_externos,
        'total_otros': total_otros,
        'desde': desde,
        'hasta': hasta,
        'empresa': empresa
    }

    return render(request, 'taller/reportes/otros_servicios_fecha.html', context)
