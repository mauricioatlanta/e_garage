"""
Vistas para el módulo de inteligencia de negocio
"""
import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F, Avg
from django.http import JsonResponse
from django.utils import timezone
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.repuesto import Repuesto
from taller.models.mecanico import Mecanico
from taller.models.perfil_usuario import PerfilUsuario


@login_required
def dashboard_business_intelligence(request):
    """Dashboard principal de inteligencia de negocio"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
    except PerfilUsuario.DoesNotExist:
        return render(request, 'error.html', {
            'error': 'No tienes un perfil de usuario configurado'
        })

    # Obtener fechas para filtros
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)  # Último mes por defecto

    # Obtener parámetros de filtro
    if request.GET.get('fecha_inicio'):
        fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
    if request.GET.get('fecha_fin'):
        fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()

    # Datos para el dashboard
    context = {
        'empresa': empresa,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'servicios_ranking': get_servicios_ranking(empresa, fecha_inicio, fecha_fin),
        'repuestos_utilidad': get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin),
        'mecanicos_stats': get_mecanicos_stats(empresa, fecha_inicio, fecha_fin),
        'resumen_general': get_resumen_general(empresa, fecha_inicio, fecha_fin),
    }

    return render(request, 'business_intelligence/dashboard.html', context)


def get_servicios_ranking(empresa, fecha_inicio, fecha_fin):
    """Obtiene el ranking de servicios más vendidos"""
    servicios = ServicioDocumento.objects.filter(
        empresa=empresa,
        documento__fecha__range=[fecha_inicio, fecha_fin]
    ).values('nombre').annotate(
        cantidad_vendida=Count('id'),
        ingresos_totales=Sum('precio'),
        precio_promedio=Avg('precio')
    ).order_by('-cantidad_vendida')[:10]

    return list(servicios)


def get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin):
    """Calcula la utilidad neta por repuesto"""
    repuestos_vendidos = RepuestoDocumento.objects.filter(
        documento__empresa=empresa,
        documento__fecha__range=[fecha_inicio, fecha_fin],
        repuesto__isnull=False
    ).select_related('repuesto').values(
        'repuesto__nombre_repuesto',
        'repuesto__part_number',
        'repuesto__precio_venta',
        'repuesto__precio_compra'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        ingresos_totales=Sum(F('cantidad') * F('precio')),
    )

    utilidades = []
    for repuesto in repuestos_vendidos:
        precio_venta = repuesto['repuesto__precio_venta']
        precio_compra = repuesto['repuesto__precio_compra']
        cantidad = repuesto['cantidad_vendida']
        ingresos = repuesto['ingresos_totales']
        
        costo_total = precio_compra * cantidad
        utilidad_bruta = ingresos - costo_total
        margen_utilidad = (utilidad_bruta / ingresos * 100) if ingresos > 0 else 0

        utilidades.append({
            'nombre': repuesto['repuesto__nombre_repuesto'],
            'part_number': repuesto['repuesto__part_number'],
            'cantidad_vendida': cantidad,
            'ingresos_totales': ingresos,
            'costo_total': costo_total,
            'utilidad_bruta': utilidad_bruta,
            'margen_utilidad': round(margen_utilidad, 2),
            'precio_venta': precio_venta,
            'precio_compra': precio_compra,
        })

    return sorted(utilidades, key=lambda x: x['utilidad_bruta'], reverse=True)[:10]


def get_mecanicos_stats(empresa, fecha_inicio, fecha_fin):
    """Obtiene estadísticas por mecánico"""
    mecanicos = Mecanico.objects.filter(empresa=empresa, activo=True)
    stats = []

    for mecanico in mecanicos:
        documentos = Documento.objects.filter(
            empresa=empresa,
            mecanico=mecanico,
            fecha__range=[fecha_inicio, fecha_fin]
        )

        # Calcular totales
        total_documentos = documentos.count()
        
        # Agregar repuestos vendidos de forma separada
        repuestos_queryset = RepuestoDocumento.objects.filter(documento__in=documentos)
        total_repuestos_cantidad = sum(r.cantidad for r in repuestos_queryset)
        total_repuestos_valor = sum(r.cantidad * r.precio for r in repuestos_queryset)

        # Agregar servicios realizados
        servicios_stats = ServicioDocumento.objects.filter(
            documento__in=documentos
        ).aggregate(
            cantidad=Count('id'),
            valor=Sum('precio')
        )

        ingresos_totales = total_repuestos_valor + (servicios_stats['valor'] or 0)

        stats.append({
            'mecanico': mecanico,
            'total_documentos': total_documentos,
            'repuestos_vendidos': total_repuestos_cantidad,
            'servicios_realizados': servicios_stats['cantidad'] or 0,
            'ingresos_totales': ingresos_totales,
            'promedio_por_documento': round(ingresos_totales / total_documentos, 2) if total_documentos > 0 else 0,
        })

    return sorted(stats, key=lambda x: x['ingresos_totales'], reverse=True)


def get_resumen_general(empresa, fecha_inicio, fecha_fin):
    """Obtiene un resumen general del período"""
    documentos = Documento.objects.filter(
        empresa=empresa,
        fecha__range=[fecha_inicio, fecha_fin]
    )

    total_repuestos = RepuestoDocumento.objects.filter(
        documento__in=documentos
    ).aggregate(
        cantidad=Sum('cantidad'),
        valor=Sum(F('cantidad') * F('precio'))
    )

    total_servicios = ServicioDocumento.objects.filter(
        documento__in=documentos
    ).aggregate(
        cantidad=Count('id'),
        valor=Sum('precio')
    )

    return {
        'total_documentos': documentos.count(),
        'total_repuestos_vendidos': total_repuestos['cantidad'] or 0,
        'valor_repuestos': total_repuestos['valor'] or 0,
        'total_servicios_realizados': total_servicios['cantidad'] or 0,
        'valor_servicios': total_servicios['valor'] or 0,
        'ingresos_totales': (total_repuestos['valor'] or 0) + (total_servicios['valor'] or 0),
        'promedio_diario': round(
            ((total_repuestos['valor'] or 0) + (total_servicios['valor'] or 0)) / 
            max((fecha_fin - fecha_inicio).days, 1), 2
        ),
    }


@login_required
def api_servicios_ranking(request):
    """API para obtener ranking de servicios en formato JSON"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
        
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
        
        if request.GET.get('fecha_inicio'):
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
        if request.GET.get('fecha_fin'):
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()

        datos = get_servicios_ranking(empresa, fecha_inicio, fecha_fin)
        return JsonResponse({'success': True, 'data': datos})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_repuestos_utilidad(request):
    """API para obtener utilidades de repuestos en formato JSON"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
        
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
        
        if request.GET.get('fecha_inicio'):
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
        if request.GET.get('fecha_fin'):
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()

        datos = get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin)
        return JsonResponse({'success': True, 'data': datos})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_mecanicos_stats(request):
    """API para obtener estadísticas de mecánicos en formato JSON"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
        
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
        
        if request.GET.get('fecha_inicio'):
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
        if request.GET.get('fecha_fin'):
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()

        datos = get_mecanicos_stats(empresa, fecha_inicio, fecha_fin)
        
        # Convertir objetos a diccionarios para JSON
        datos_json = []
        for stat in datos:
            datos_json.append({
                'mecanico_nombre': stat['mecanico'].nombre,
                'total_documentos': stat['total_documentos'],
                'repuestos_vendidos': stat['repuestos_vendidos'],
                'servicios_realizados': stat['servicios_realizados'],
                'ingresos_totales': stat['ingresos_totales'],
                'promedio_por_documento': stat['promedio_por_documento'],
            })
        
        return JsonResponse({'success': True, 'data': datos_json})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
