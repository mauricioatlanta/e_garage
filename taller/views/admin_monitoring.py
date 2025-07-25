"""
Panel interno de monitoreo de suscripciones con filtros avanzados
Vista administrativa para gestión y análisis de suscripciones
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, timedelta
import csv
import json

from taller.models import Empresa, TrialRegistro, ComprobantePago
from django.contrib.auth.models import User
from taller.utils.smart_logging import smart_logger


@staff_member_required
def subscription_dashboard(request):
    """Panel principal de monitoreo de suscripciones"""
    
    # Estadísticas generales
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    stats = {
        'total_empresas': Empresa.objects.count(),
        'activas': Empresa.objects.filter(estado_suscripcion='activa').count(),
        'vencidas': Empresa.objects.filter(estado_suscripcion='vencida').count(),
        'suspendidas': Empresa.objects.filter(estado_suscripcion='suspendida').count(),
        'canceladas': Empresa.objects.filter(estado_suscripcion='cancelada').count(),
        'trials_activos': TrialRegistro.objects.filter(activo=True).count(),
        'trials_expirados': TrialRegistro.objects.filter(activo=False).count(),
        'nuevas_este_mes': Empresa.objects.filter(fecha_registro__gte=thirty_days_ago).count(),
    }
    
    # Empresas que vencen pronto (próximos 15 días)
    expiring_soon = Empresa.objects.filter(
        estado_suscripcion='activa',
        fecha_vencimiento_suscripcion__lte=today + timedelta(days=15),
        fecha_vencimiento_suscripcion__gt=today
    ).order_by('fecha_vencimiento_suscripcion')
    
    # Trials que expiran pronto (próximos 7 días)
    trials_expiring = TrialRegistro.objects.filter(
        activo=True,
        fecha_expiracion__lte=today + timedelta(days=7),
        fecha_expiracion__gt=today
    ).order_by('fecha_expiracion')
    
    # Ingresos del mes
    current_month_payments = ComprobantePago.objects.filter(
        fecha_upload__year=today.year,
        fecha_upload__month=today.month,
        aprobado=True
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    context = {
        'stats': stats,
        'expiring_soon': expiring_soon[:10],  # Mostrar solo los 10 más próximos
        'trials_expiring': trials_expiring[:10],
        'current_month_revenue': current_month_payments,
        'today': today,
    }
    
    return render(request, 'admin_panel/subscription_dashboard.html', context)


@staff_member_required
def subscription_list(request):
    """Lista detallada de suscripciones con filtros avanzados"""
    
    # Obtener parámetros de filtro
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    trial_filter = request.GET.get('trial', '')
    payment_status = request.GET.get('payment', '')
    sort_by = request.GET.get('sort', '-fecha_registro')
    
    # Query base
    empresas = Empresa.objects.select_related('usuario').prefetch_related('comprobantepago_set')
    
    # Aplicar filtros
    if status_filter:
        empresas = empresas.filter(estado_suscripcion=status_filter)
    
    if search_query:
        empresas = empresas.filter(
            Q(nombre__icontains=search_query) |
            Q(usuario__username__icontains=search_query) |
            Q(usuario__email__icontains=search_query) |
            Q(usuario__first_name__icontains=search_query) |
            Q(usuario__last_name__icontains=search_query)
        )
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            empresas = empresas.filter(fecha_registro__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            empresas = empresas.filter(fecha_registro__lte=date_to_parsed)
        except ValueError:
            pass
    
    if trial_filter == 'active':
        # Solo empresas con trial activo
        trial_ids = TrialRegistro.objects.filter(activo=True).values_list('empresa_id', flat=True)
        empresas = empresas.filter(id__in=trial_ids)
    elif trial_filter == 'expired':
        # Solo empresas con trial expirado
        trial_ids = TrialRegistro.objects.filter(activo=False).values_list('empresa_id', flat=True)
        empresas = empresas.filter(id__in=trial_ids)
    
    if payment_status == 'pending':
        # Empresas con pagos pendientes
        pending_payment_ids = ComprobantePago.objects.filter(
            aprobado=False
        ).values_list('empresa_id', flat=True)
        empresas = empresas.filter(id__in=pending_payment_ids)
    
    # Ordenamiento
    valid_sort_fields = [
        'fecha_registro', '-fecha_registro',
        'nombre', '-nombre',
        'estado_suscripcion', '-estado_suscripcion',
        'fecha_vencimiento_suscripcion', '-fecha_vencimiento_suscripcion'
    ]
    if sort_by in valid_sort_fields:
        empresas = empresas.order_by(sort_by)
    
    # Paginación
    paginator = Paginator(empresas, 25)  # 25 empresas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contexto para filtros
    status_choices = [
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
        ('suspendida', 'Suspendida'),
        ('cancelada', 'Cancelada'),
    ]
    
    trial_choices = [
        ('active', 'Trial Activo'),
        ('expired', 'Trial Expirado'),
    ]
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'trial_choices': trial_choices,
        'current_filters': {
            'status': status_filter,
            'search': search_query,
            'date_from': date_from,
            'date_to': date_to,
            'trial': trial_filter,
            'payment': payment_status,
            'sort': sort_by,
        },
        'total_count': paginator.count,
    }
    
    return render(request, 'admin_panel/subscription_list.html', context)


@staff_member_required
def subscription_analytics(request):
    """Analytics avanzados de suscripciones"""
    
    today = timezone.now().date()
    
    # Análisis temporal (últimos 12 meses)
    monthly_data = []
    for i in range(12):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        # Nuevas suscripciones
        nuevas = Empresa.objects.filter(
            fecha_registro__gte=month_start,
            fecha_registro__lte=month_end
        ).count()
        
        # Cancelaciones
        canceladas = Empresa.objects.filter(
            estado_suscripcion='cancelada',
            fecha_modificacion__gte=month_start,
            fecha_modificacion__lte=month_end
        ).count()
        
        # Ingresos
        ingresos = ComprobantePago.objects.filter(
            fecha_upload__gte=month_start,
            fecha_upload__lte=month_end,
            aprobado=True
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        monthly_data.append({
            'month': month_date.strftime('%Y-%m'),
            'month_name': month_date.strftime('%B %Y'),
            'nuevas': nuevas,
            'canceladas': canceladas,
            'ingresos': float(ingresos),
            'neto': nuevas - canceladas
        })
    
    monthly_data.reverse()  # Orden cronológico
    
    # Análisis de conversión de trials
    total_trials = TrialRegistro.objects.count()
    trials_convertidos = TrialRegistro.objects.filter(
        empresa__estado_suscripcion='activa'
    ).count()
    conversion_rate = (trials_convertidos / total_trials * 100) if total_trials > 0 else 0
    
    # Análisis de retención
    empresas_activas_30_dias = Empresa.objects.filter(
        estado_suscripcion='activa',
        fecha_registro__lte=today - timedelta(days=30)
    ).count()
    
    total_empresas_30_dias = Empresa.objects.filter(
        fecha_registro__lte=today - timedelta(days=30)
    ).count()
    
    retention_rate = (empresas_activas_30_dias / total_empresas_30_dias * 100) if total_empresas_30_dias > 0 else 0
    
    # Top empresas por ingresos
    top_empresas = Empresa.objects.annotate(
        total_pagos=Sum('comprobantepago__monto', filter=Q(comprobantepago__aprobado=True))
    ).filter(total_pagos__isnull=False).order_by('-total_pagos')[:10]
    
    context = {
        'monthly_data': monthly_data,
        'conversion_rate': round(conversion_rate, 2),
        'retention_rate': round(retention_rate, 2),
        'total_trials': total_trials,
        'trials_convertidos': trials_convertidos,
        'top_empresas': top_empresas,
    }
    
    return render(request, 'admin_panel/subscription_analytics.html', context)


@staff_member_required
def subscription_detail(request, empresa_id):
    """Vista detallada de una suscripción específica"""
    
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Trial asociado
    trial = TrialRegistro.objects.filter(empresa=empresa).first()
    
    # Historial de pagos
    pagos = ComprobantePago.objects.filter(empresa=empresa).order_by('-fecha_upload')
    
    # Estadísticas de uso (esto requeriría modelos adicionales de tracking)
    # Por ahora, datos básicos
    
    context = {
        'empresa': empresa,
        'trial': trial,
        'pagos': pagos,
        'total_pagos': pagos.filter(aprobado=True).aggregate(total=Sum('monto'))['total'] or 0,
        'pagos_pendientes': pagos.filter(aprobado=False).count(),
    }
    
    return render(request, 'admin_panel/subscription_detail.html', context)


@staff_member_required
def subscription_actions(request, empresa_id):
    """Acciones administrativas sobre suscripciones"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    empresa = get_object_or_404(Empresa, id=empresa_id)
    action = request.POST.get('action')
    
    if action == 'suspend':
        old_status = empresa.estado_suscripcion
        empresa.estado_suscripcion = 'suspendida'
        empresa.save()
        
        smart_logger.log_subscription_change(
            empresa_id=empresa.id,
            old_status=old_status,
            new_status='suspendida',
            reason=f"Suspensión manual por admin: {request.user.username}"
        )
        
        return JsonResponse({'success': True, 'message': 'Empresa suspendida correctamente'})
    
    elif action == 'activate':
        old_status = empresa.estado_suscripcion
        empresa.estado_suscripcion = 'activa'
        empresa.save()
        
        smart_logger.log_subscription_change(
            empresa_id=empresa.id,
            old_status=old_status,
            new_status='activa',
            reason=f"Activación manual por admin: {request.user.username}"
        )
        
        return JsonResponse({'success': True, 'message': 'Empresa activada correctamente'})
    
    elif action == 'extend':
        days = int(request.POST.get('days', 30))
        empresa.extender_suscripcion(days)
        
        smart_logger.log_subscription_change(
            empresa_id=empresa.id,
            old_status=empresa.estado_suscripcion,
            new_status=empresa.estado_suscripcion,
            reason=f"Extensión de {days} días por admin: {request.user.username}"
        )
        
        return JsonResponse({'success': True, 'message': f'Suscripción extendida {days} días'})
    
    else:
        return JsonResponse({'error': 'Acción no válida'}, status=400)


@staff_member_required
def export_subscriptions(request):
    """Exportar datos de suscripciones a CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="suscripciones_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Empresa', 'Usuario', 'Email', 'Estado', 'Fecha Registro',
        'Fecha Vencimiento', 'Total Pagos', 'Trial Activo'
    ])
    
    # Aplicar filtros si existen
    empresas = Empresa.objects.select_related('usuario').all()
    status_filter = request.GET.get('status')
    if status_filter:
        empresas = empresas.filter(estado_suscripcion=status_filter)
    
    for empresa in empresas:
        trial_activo = TrialRegistro.objects.filter(empresa=empresa, activo=True).exists()
        total_pagos = empresa.comprobantepago_set.filter(aprobado=True).aggregate(
            total=Sum('monto'))['total'] or 0
        
        writer.writerow([
            empresa.id,
            empresa.nombre,
            empresa.usuario.username,
            empresa.usuario.email,
            empresa.estado_suscripcion,
            empresa.fecha_registro.strftime('%Y-%m-%d'),
            empresa.fecha_vencimiento_suscripcion.strftime('%Y-%m-%d') if empresa.fecha_vencimiento_suscripcion else '',
            total_pagos,
            'Sí' if trial_activo else 'No'
        ])
    
    return response


@staff_member_required
def subscription_api_stats(request):
    """API endpoint para estadísticas en tiempo real (para gráficos AJAX)"""
    
    today = timezone.now().date()
    
    # Estadísticas por estado
    stats_by_status = Empresa.objects.values('estado_suscripcion').annotate(
        count=Count('id')
    )
    
    # Nuevas suscripciones por día (últimos 30 días)
    daily_new = []
    for i in range(30):
        date = today - timedelta(days=i)
        count = Empresa.objects.filter(fecha_registro=date).count()
        daily_new.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    daily_new.reverse()
    
    data = {
        'stats_by_status': list(stats_by_status),
        'daily_new': daily_new,
        'last_updated': timezone.now().isoformat()
    }
    
    return JsonResponse(data)
