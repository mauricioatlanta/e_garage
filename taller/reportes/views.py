
from django.shortcuts import render
from taller.models.documento import ServicioDocumento, Documento
from taller.models.vehiculos import Vehiculo
from taller.models.modelo import Modelo
from taller.models.marca import Marca
from taller.models.clientes import Cliente
from collections import defaultdict
from datetime import timedelta, date
from django.db.models import Sum, Count, F

def reportes_dashboard(request):
    return render(request, 'taller/reportes/reportes.html')

def reporte_repuestos(request):
    from django.db.models import Sum, F, FloatField, ExpressionWrapper
    from taller.models.documento import RepuestoDocumento
    from taller.models.repuesto import Repuesto
    from collections import defaultdict
    # Top 10 repuestos más vendidos
    repuesto_ventas = (
        RepuestoDocumento.objects
        .values('codigo', 'nombre')
        .annotate(cantidad_total=Sum('cantidad'), ingresos=Sum(ExpressionWrapper(F('cantidad') * F('precio'), output_field=FloatField())))
        .order_by('-cantidad_total')
    )
    top_repuestos = list(repuesto_ventas[:10])

    # Repuestos con mayor margen de ganancia (requiere precio_venta y precio_compra en Repuesto)
    top_margen = []
    from django.db.models import Q
    for r in Repuesto.objects.all():
        vendidos = RepuestoDocumento.objects.filter(codigo=r.part_number)
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

    # Repuestos con bajo stock (stock <= 5)
    bajo_stock = Repuesto.objects.filter(stock__lte=5).values('part_number', 'nombre_repuesto', 'stock')
    bajo_stock = [{'codigo': r['part_number'], 'nombre': r['nombre_repuesto'], 'stock': r['stock']} for r in bajo_stock]

    # Histórico de ventas mensuales
    ventas = (
        RepuestoDocumento.objects
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

    # Repuestos nunca vendidos
    vendidos_codigos = set(RepuestoDocumento.objects.values_list('codigo', flat=True))
    nunca_vendidos = Repuesto.objects.exclude(part_number__in=vendidos_codigos)
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
    # Panel de facturación
    # Total
    facturacion_total = ServicioDocumento.objects.aggregate(total=Sum('precio'))['total'] or 0
    # Por periodo (últimos 6 meses)
    from datetime import date, timedelta
    hoy = date.today()
    hace_6_meses = hoy - timedelta(days=180)
    facturacion_periodo_qs = (
        ServicioDocumento.objects
        .filter(documento__fecha__gte=hace_6_meses)
        .annotate(mes=F('documento__fecha'))
        .values('mes')
        .annotate(total=Sum('precio'))
        .order_by('mes')
    )
    facturacion_periodo = [
        {'mes': f['mes'].strftime('%Y-%m') if f['mes'] else 'Sin fecha', 'total': f['total']} for f in facturacion_periodo_qs
    ]
    # Por servicio
    facturacion_servicio = list(
        ServicioDocumento.objects
        .values('nombre')
        .annotate(total=Sum('precio'))
        .order_by('-total')[:10]
    )
    for f in facturacion_servicio:
        f['nombre'] = f['nombre'] or 'Sin nombre'
    # Por cliente
    facturacion_cliente_qs = (
        ServicioDocumento.objects
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

    # Top 10 servicios más vendidos
    top_servicios = (
        ServicioDocumento.objects
        .values('nombre')
        .annotate(cantidad=Count('id'), total=Sum('precio'))
        .order_by('-cantidad')[:10]
    )

    # Servicios con mayor facturación
    top_facturacion = (
        ServicioDocumento.objects
        .values('nombre')
        .annotate(total=Sum('precio'), cantidad=Count('id'))
        .order_by('-total')[:10]
    )

    # Histórico de servicios mensuales
    servicios_mes = (
        ServicioDocumento.objects
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
