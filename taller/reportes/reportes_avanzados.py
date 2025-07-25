"""
📊 REPORTES AVANZADOS CON SERVICIOS SUBCONTRATADOS
================================================

Reportes visuales para análisis de rentabilidad y servicios externos
"""

from django.shortcuts import render
from django.db.models import Sum, Count, F, Avg, Q, Max, Min
from django.db.models import ExpressionWrapper, FloatField
from collections import defaultdict
from datetime import date, timedelta
from django.db import models

from taller.models.documento import (
    Documento, ServicioDocumento, OtroServicioDocumento, RepuestoDocumento
)
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


def reportes_rentabilidad(request):
    """
    🎯 Reporte de rentabilidad por tipo de servicio
    """
    # Servicios internos - rentabilidad
    servicios_internos = (
        ServicioDocumento.objects
        .filter(documento__tipo_documento='Factura')
        .values('nombre')
        .annotate(
            cantidad=Count('id'),
            ingresos_totales=Sum('precio'),
            precio_promedio=Avg('precio')
        )
        .order_by('-ingresos_totales')[:15]
    )
    
    # Servicios subcontratados - análisis de rentabilidad
    servicios_externos = (
        OtroServicioDocumento.objects
        .filter(documento__tipo_documento='Factura')
        .values('nombre_servicio', 'empresa_externa')
        .annotate(
            cantidad=Count('id'),
            costos_totales=Sum('costo_interno'),
            ingresos_totales=Sum('precio_cliente'),
            ganancia_total=Sum(F('precio_cliente') - F('costo_interno')),
            margen_promedio=Avg(
                ExpressionWrapper(
                    (F('precio_cliente') - F('costo_interno')) * 100.0 / F('precio_cliente'),
                    output_field=FloatField()
                )
            )
        )
        .order_by('-ganancia_total')[:15]
    )
    
    # Comparativa rentabilidad: interno vs externo
    total_interno = ServicioDocumento.objects.filter(
        documento__tipo_documento='Factura'
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    total_externo_ingresos = OtroServicioDocumento.objects.filter(
        documento__tipo_documento='Factura'
    ).aggregate(total=Sum('precio_cliente'))['total'] or 0
    
    total_externo_costos = OtroServicioDocumento.objects.filter(
        documento__tipo_documento='Factura'
    ).aggregate(total=Sum('costo_interno'))['total'] or 0
    
    ganancia_externa = total_externo_ingresos - total_externo_costos
    
    # Top proveedores externos por volumen
    top_proveedores = (
        OtroServicioDocumento.objects
        .filter(documento__tipo_documento='Factura')
        .values('empresa_externa')
        .annotate(
            cantidad_servicios=Count('id'),
            volumen_total=Sum('precio_cliente'),
            costo_total=Sum('costo_interno'),
            ganancia_total=Sum(F('precio_cliente') - F('costo_interno'))
        )
        .order_by('-volumen_total')[:10]
    )
    
    # Servicios más rentables (margen %)
    servicios_alto_margen = []
    for servicio in OtroServicioDocumento.objects.filter(documento__tipo_documento='Factura'):
        if servicio.precio_cliente > 0:
            margen = ((servicio.precio_cliente - servicio.costo_interno) / servicio.precio_cliente) * 100
            servicios_alto_margen.append({
                'nombre': servicio.nombre_servicio,
                'proveedor': servicio.empresa_externa,
                'margen': round(margen, 2),
                'ganancia': servicio.ganancia,
                'precio_cliente': servicio.precio_cliente,
                'costo_interno': servicio.costo_interno
            })
    
    servicios_alto_margen = sorted(servicios_alto_margen, key=lambda x: x['margen'], reverse=True)[:10]
    
    context = {
        'servicios_internos': servicios_internos,
        'servicios_externos': servicios_externos,
        'total_interno': total_interno,
        'total_externo_ingresos': total_externo_ingresos,
        'total_externo_costos': total_externo_costos,
        'ganancia_externa': ganancia_externa,
        'top_proveedores': top_proveedores,
        'servicios_alto_margen': servicios_alto_margen,
    }
    
    return render(request, 'taller/reportes/rentabilidad.html', context)


def reporte_comparativo_precios(request):
    """
    💰 Comparativa precio cliente vs. costo proveedor
    """
    # Análisis detallado por servicio
    analisis_servicios = []
    
    servicios_unicos = (
        OtroServicioDocumento.objects
        .filter(documento__tipo_documento='Factura')
        .values('nombre_servicio')
        .distinct()
    )
    
    for servicio in servicios_unicos:
        nombre = servicio['nombre_servicio']
        registros = OtroServicioDocumento.objects.filter(
            nombre_servicio=nombre,
            documento__tipo_documento='Factura'
        )
        
        stats = registros.aggregate(
            cantidad=Count('id'),
            precio_promedio=Avg('precio_cliente'),
            costo_promedio=Avg('costo_interno'),
            precio_max=Max('precio_cliente'),
            precio_min=Min('precio_cliente'),
            costo_max=Max('costo_interno'),
            costo_min=Min('costo_interno'),
            ganancia_total=Sum(F('precio_cliente') - F('costo_interno'))
        )
        
        if stats['precio_promedio'] and stats['costo_promedio']:
            margen_promedio = ((stats['precio_promedio'] - stats['costo_promedio']) / stats['precio_promedio']) * 100
            
            analisis_servicios.append({
                'nombre': nombre,
                'cantidad': stats['cantidad'],
                'precio_promedio': round(stats['precio_promedio'], 2),
                'costo_promedio': round(stats['costo_promedio'], 2),
                'margen_promedio': round(margen_promedio, 2),
                'ganancia_total': stats['ganancia_total'],
                'precio_rango': f"${stats['precio_min']:,} - ${stats['precio_max']:,}",
                'costo_rango': f"${stats['costo_min']:,} - ${stats['costo_max']:,}"
            })
    
    analisis_servicios = sorted(analisis_servicios, key=lambda x: x['ganancia_total'], reverse=True)
    
    # Alertas de márgenes bajos
    margenes_bajos = [s for s in analisis_servicios if s['margen_promedio'] < 20]
    
    # Evolución mensual de márgenes
    hoy = date.today()
    hace_6_meses = hoy - timedelta(days=180)
    
    evolucion_mensual = (
        OtroServicioDocumento.objects
        .filter(
            documento__tipo_documento='Factura',
            documento__fecha__gte=hace_6_meses
        )
        .annotate(mes=F('documento__fecha__year') * 100 + F('documento__fecha__month'))
        .values('mes')
        .annotate(
            ingresos=Sum('precio_cliente'),
            costos=Sum('costo_interno'),
            ganancia=Sum(F('precio_cliente') - F('costo_interno'))
        )
        .order_by('mes')
    )
    
    context = {
        'analisis_servicios': analisis_servicios,
        'margenes_bajos': margenes_bajos,
        'evolucion_mensual': list(evolucion_mensual),
    }
    
    return render(request, 'taller/reportes/comparativo_precios.html', context)


def reporte_servicios_subcontratados(request):
    """
    🔧 Servicios subcontratados más frecuentes
    """
    # Servicios más frecuentes
    servicios_frecuentes = (
        OtroServicioDocumento.objects
        .values('nombre_servicio')
        .annotate(
            frecuencia=Count('id'),
            volumen_total=Sum('precio_cliente'),
            ganancia_total=Sum(F('precio_cliente') - F('costo_interno'))
        )
        .order_by('-frecuencia')[:15]
    )
    
    # Proveedores más utilizados
    proveedores_frecuentes = (
        OtroServicioDocumento.objects
        .values('empresa_externa')
        .annotate(
            servicios_realizados=Count('id'),
            tipos_servicios=Count('nombre_servicio', distinct=True),
            volumen_total=Sum('precio_cliente'),
            ganancia_generada=Sum(F('precio_cliente') - F('costo_interno'))
        )
        .order_by('-servicios_realizados')[:10]
    )
    
    # Análisis temporal - últimos 6 meses
    hoy = date.today()
    hace_6_meses = hoy - timedelta(days=180)
    
    tendencia_mensual = defaultdict(lambda: {'cantidad': 0, 'volumen': 0})
    
    servicios_periodo = OtroServicioDocumento.objects.filter(
        documento__fecha__gte=hace_6_meses
    )
    
    for servicio in servicios_periodo:
        mes_key = servicio.documento.fecha.strftime('%Y-%m') if servicio.documento.fecha else 'Sin fecha'
        tendencia_mensual[mes_key]['cantidad'] += 1
        tendencia_mensual[mes_key]['volumen'] += servicio.precio_cliente
    
    # Preparar datos para gráficos
    meses = sorted(tendencia_mensual.keys())
    cantidades = [tendencia_mensual[mes]['cantidad'] for mes in meses]
    volumenes = [tendencia_mensual[mes]['volumen'] for mes in meses]
    
    # Distribución por tipo de vehículo
    vehiculos_servicios = (
        OtroServicioDocumento.objects
        .filter(documento__vehiculo__isnull=False)
        .values('documento__vehiculo__marca__nombre', 'documento__vehiculo__modelo__nombre')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:10]
    )
    
    # Clientes que más usan servicios externos
    clientes_externos = (
        OtroServicioDocumento.objects
        .values('documento__cliente__nombre', 'documento__cliente__apellido')
        .annotate(
            servicios_externos=Count('id'),
            gasto_total=Sum('precio_cliente')
        )
        .order_by('-servicios_externos')[:10]
    )
    
    for cliente in clientes_externos:
        nombre = cliente['documento__cliente__nombre'] or ''
        apellido = cliente['documento__cliente__apellido'] or ''
        cliente['nombre_completo'] = f"{nombre} {apellido}".strip()
    
    context = {
        'servicios_frecuentes': servicios_frecuentes,
        'proveedores_frecuentes': proveedores_frecuentes,
        'tendencia_meses': meses,
        'tendencia_cantidades': cantidades,
        'tendencia_volumenes': volumenes,
        'vehiculos_servicios': vehiculos_servicios,
        'clientes_externos': clientes_externos,
    }
    
    return render(request, 'taller/reportes/servicios_subcontratados.html', context)


def dashboard_rentabilidad(request):
    """
    📈 Dashboard general de rentabilidad
    """
    # KPIs principales
    total_facturado = (
        ServicioDocumento.objects.filter(documento__tipo_documento='Factura')
        .aggregate(total=Sum('precio'))['total'] or 0
    ) + (
        OtroServicioDocumento.objects.filter(documento__tipo_documento='Factura')
        .aggregate(total=Sum('precio_cliente'))['total'] or 0
    )
    
    costos_externos = (
        OtroServicioDocumento.objects.filter(documento__tipo_documento='Factura')
        .aggregate(total=Sum('costo_interno'))['total'] or 0
    )
    
    ganancia_neta = total_facturado - costos_externos
    margen_general = (ganancia_neta / total_facturado * 100) if total_facturado > 0 else 0
    
    # Distribución de ingresos
    ingresos_internos = ServicioDocumento.objects.filter(
        documento__tipo_documento='Factura'
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    ingresos_externos = OtroServicioDocumento.objects.filter(
        documento__tipo_documento='Factura'
    ).aggregate(total=Sum('precio_cliente'))['total'] or 0
    
    # Mejores y peores márgenes
    mejor_proveedor = (
        OtroServicioDocumento.objects
        .filter(documento__tipo_documento='Factura')
        .values('empresa_externa')
        .annotate(
            margen_promedio=Avg(
                ExpressionWrapper(
                    (F('precio_cliente') - F('costo_interno')) * 100.0 / F('precio_cliente'),
                    output_field=FloatField()
                )
            )
        )
        .order_by('-margen_promedio')
        .first()
    )
    
    peor_proveedor = (
        OtroServicioDocumento.objects
        .filter(documento__tipo_documento='Factura')
        .values('empresa_externa')
        .annotate(
            margen_promedio=Avg(
                ExpressionWrapper(
                    (F('precio_cliente') - F('costo_interno')) * 100.0 / F('precio_cliente'),
                    output_field=FloatField()
                )
            )
        )
        .order_by('margen_promedio')
        .first()
    )
    
    context = {
        'total_facturado': total_facturado,
        'costos_externos': costos_externos,
        'ganancia_neta': ganancia_neta,
        'margen_general': round(margen_general, 2),
        'ingresos_internos': ingresos_internos,
        'ingresos_externos': ingresos_externos,
        'mejor_proveedor': mejor_proveedor,
        'peor_proveedor': peor_proveedor,
    }
    
    return render(request, 'taller/reportes/dashboard_rentabilidad.html', context)
