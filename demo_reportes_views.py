from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q
from datetime import datetime, timedelta
from taller.models.documento import Documento, ServicioDocumento, RepuestoDocumento

def demo_reportes_por_fecha(request):
    """Vista demo sin autenticación para mostrar reportes por fecha"""
    
    # Obtener parámetros de fecha
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')
    tipo_reporte = request.GET.get('tipo', 'resumen')
    
    # Si no hay fechas, usar últimos 30 días
    if not desde or not hasta:
        hasta_date = datetime.now().date()
        desde_date = hasta_date - timedelta(days=30)
    else:
        try:
            desde_date = datetime.strptime(desde, '%Y-%m-%d').date()
            hasta_date = datetime.strptime(hasta, '%Y-%m-%d').date()
        except ValueError:
            hasta_date = datetime.now().date()
            desde_date = hasta_date - timedelta(days=30)
    
    # Documentos en el rango
    documentos = Documento.objects.filter(
        fecha__range=[desde_date, hasta_date]
    )
    
    # Estadísticas generales
    total_documentos = documentos.count()
    
    # Servicios
    servicios = ServicioDocumento.objects.filter(
        documento__fecha__range=[desde_date, hasta_date]
    )
    total_servicios = servicios.aggregate(
        cantidad=Count('id'),
        valor_total=Sum('precio')
    )
    
    # Repuestos
    repuestos = RepuestoDocumento.objects.filter(
        documento__fecha__range=[desde_date, hasta_date]
    )
    total_repuestos = repuestos.aggregate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum(F('cantidad') * F('precio'))
    )
    
    # Top servicios
    top_servicios = servicios.values('nombre').annotate(
        total_veces=Count('id'),
        valor_total=Sum('precio')
    ).order_by('-total_veces')[:10]
    
    # Top repuestos
    top_repuestos = repuestos.values('nombre', 'codigo').annotate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum(F('cantidad') * F('precio'))
    ).order_by('-cantidad_total')[:10]
    
    # Documentos recientes
    docs_recientes = documentos.select_related('cliente', 'vehiculo').order_by('-fecha')[:10]
    
    context = {
        'desde': desde_date.strftime('%Y-%m-%d'),
        'hasta': hasta_date.strftime('%Y-%m-%d'),
        'total_documentos': total_documentos,
        'total_servicios': total_servicios,
        'total_repuestos': total_repuestos,
        'top_servicios': top_servicios,
        'top_repuestos': top_repuestos,
        'docs_recientes': docs_recientes,
        'tipo_reporte': tipo_reporte
    }
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(context, safe=False)
    
    return render(request, 'taller/reportes/demo_reportes_por_fecha.html', context)
