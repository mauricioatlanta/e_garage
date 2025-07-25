"""
Dashboard de Suscriptores - Vista Administrativa
Funcionalidades:
- Vista completa de todos los suscriptores
- Estadísticas por país (Chile/USA)
- Tipos de suscripción y estados
- Nuevos registros por período
- Alertas de expiración
- Exportación de datos
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib import messages
from taller.models.empresa import Empresa
from taller.models.trial import TrialRegistro
from taller.models.comprobante_pago import ComprobantePago
from collections import defaultdict
import csv
import json

# Decorador para verificar que es staff/admin
def es_staff_o_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(es_staff_o_admin)
def dashboard_admin(request):
    """
    Dashboard principal para administradores
    Muestra métricas completas de suscriptores
    """
    
    # === ESTADÍSTICAS GENERALES ===
    total_empresas = Empresa.objects.count()
    empresas_activas = Empresa.objects.filter(suscripcion_activa=True).count()
    empresas_trial = Empresa.objects.filter(plan='trial').count()
    empresas_premium = Empresa.objects.filter(plan__in=['basic', 'premium', 'enterprise']).count()
    
    # === DISTRIBUCIÓN POR PAÍS ===
    empresas_chile = Empresa.objects.filter(pais='CL').count()
    empresas_usa = Empresa.objects.filter(pais='US').count()
    
    # === ESTADÍSTICAS POR PLAN ===
    stats_planes = Empresa.objects.values('plan').annotate(
        total=Count('id'),
        activas=Count('id', filter=Q(suscripcion_activa=True))
    ).order_by('plan')
    
    # === NUEVOS SUSCRIPTORES ===
    ahora = timezone.now()
    hace_7_dias = ahora - timedelta(days=7)
    hace_30_dias = ahora - timedelta(days=30)
    hace_90_dias = ahora - timedelta(days=90)
    
    nuevos_7_dias = Empresa.objects.filter(fecha_inicio__gte=hace_7_dias).count()
    nuevos_30_dias = Empresa.objects.filter(fecha_inicio__gte=hace_30_dias).count()
    nuevos_90_dias = Empresa.objects.filter(fecha_inicio__gte=hace_90_dias).count()
    
    # === ALERTAS DE EXPIRACIÓN ===
    hoy = timezone.now().date()
    proximos_3_dias = hoy + timedelta(days=3)
    proximos_7_dias = hoy + timedelta(days=7)
    
    por_vencer_3_dias = Empresa.objects.filter(
        fecha_fin__lte=proximos_3_dias,
        fecha_fin__gte=hoy,
        suscripcion_activa=True
    ).count()
    
    por_vencer_7_dias = Empresa.objects.filter(
        fecha_fin__lte=proximos_7_dias,
        fecha_fin__gte=hoy,
        suscripcion_activa=True
    ).count()
    
    vencidas = Empresa.objects.filter(
        fecha_fin__lt=hoy,
        suscripcion_activa=True
    ).count()
    
    # === ÚLTIMOS REGISTRADOS ===
    ultimos_registros = Empresa.objects.select_related('user').order_by('-fecha_inicio')[:10]
    
    # === ESTADÍSTICAS DE TRIAL ===
    trials_pendientes = TrialRegistro.objects.filter(
        prueba_activa=False,
        prueba_expirada=False
    ).count()
    
    trials_activos = TrialRegistro.objects.filter(prueba_activa=True).count()
    trials_expirados = TrialRegistro.objects.filter(prueba_expirada=True).count()
    
    # === INGRESOS POTENCIALES ===
    ingresos_mes_actual = Empresa.objects.filter(
        suscripcion_activa=True,
        plan__in=['basic', 'premium', 'enterprise']
    ).aggregate(
        total=Count('id')
    )['total'] or 0
    
    # Estimación de ingresos (valores aproximados)
    ingresos_estimados = {
        'mensual': ingresos_mes_actual * 25000,  # CLP aproximado
        'anual': ingresos_mes_actual * 200000,   # CLP aproximado
    }
    
    # === TENDENCIAS POR SEMANA ===
    # Últimas 8 semanas de registros
    tendencias_semanales = []
    for i in range(8):
        inicio_semana = ahora - timedelta(weeks=i+1)
        fin_semana = ahora - timedelta(weeks=i)
        nuevos_semana = Empresa.objects.filter(
            fecha_inicio__gte=inicio_semana,
            fecha_inicio__lt=fin_semana
        ).count()
        tendencias_semanales.append({
            'semana': f'Semana -{i+1}',
            'nuevos': nuevos_semana,
            'fecha_inicio': inicio_semana.strftime('%d/%m')
        })
    
    tendencias_semanales.reverse()  # Más antigua a más reciente
    
    context = {
        # Estadísticas generales
        'total_empresas': total_empresas,
        'empresas_activas': empresas_activas,
        'empresas_trial': empresas_trial,
        'empresas_premium': empresas_premium,
        
        # Distribución geográfica
        'empresas_chile': empresas_chile,
        'empresas_usa': empresas_usa,
        
        # Estadísticas por plan
        'stats_planes': stats_planes,
        
        # Nuevos suscriptores
        'nuevos_7_dias': nuevos_7_dias,
        'nuevos_30_dias': nuevos_30_dias,
        'nuevos_90_dias': nuevos_90_dias,
        
        # Alertas
        'por_vencer_3_dias': por_vencer_3_dias,
        'por_vencer_7_dias': por_vencer_7_dias,
        'vencidas': vencidas,
        
        # Últimos registros
        'ultimos_registros': ultimos_registros,
        
        # Trials
        'trials_pendientes': trials_pendientes,
        'trials_activos': trials_activos,
        'trials_expirados': trials_expirados,
        
        # Ingresos
        'ingresos_estimados': ingresos_estimados,
        
        # Tendencias
        'tendencias_semanales': tendencias_semanales,
        
        # Fecha actual
        'fecha_actual': ahora,
    }
    
    return render(request, 'analytics/dashboard_admin.html', context)


@login_required
@user_passes_test(es_staff_o_admin)
def api_admin_charts(request):
    """
    API para datos de gráficos del dashboard admin
    """
    chart_type = request.GET.get('type', 'paises')
    
    if chart_type == 'paises':
        # Distribución por países
        chile_count = Empresa.objects.filter(pais='CL').count()
        usa_count = Empresa.objects.filter(pais='US').count()
        
        data = {
            'labels': ['Chile 🇨🇱', 'USA 🇺🇸'],
            'datasets': [{
                'data': [chile_count, usa_count],
                'backgroundColor': ['#00ff88', '#0066ff'],
                'borderColor': ['#00ff88', '#0066ff'],
                'borderWidth': 2
            }]
        }
        
    elif chart_type == 'planes':
        # Distribución por planes
        planes_data = Empresa.objects.values('plan').annotate(count=Count('id'))
        
        labels = []
        counts = []
        colors = ['#b347d9', '#00f5ff', '#ff00ff', '#00ff88']
        
        for i, item in enumerate(planes_data):
            plan_name = dict(Empresa.PLAN_CHOICES).get(item['plan'], item['plan'])
            labels.append(plan_name)
            counts.append(item['count'])
        
        data = {
            'labels': labels,
            'datasets': [{
                'data': counts,
                'backgroundColor': colors[:len(counts)],
                'borderColor': colors[:len(counts)],
                'borderWidth': 2
            }]
        }
        
    elif chart_type == 'estados':
        # Estados de suscripción
        activas = Empresa.objects.filter(suscripcion_activa=True).count()
        inactivas = Empresa.objects.filter(suscripcion_activa=False).count()
        
        # Calcular por vencer
        hoy = timezone.now().date()
        proximos_7_dias = hoy + timedelta(days=7)
        por_vencer = Empresa.objects.filter(
            fecha_fin__lte=proximos_7_dias,
            fecha_fin__gte=hoy,
            suscripcion_activa=True
        ).count()
        
        data = {
            'labels': ['Activas', 'Por vencer (7 días)', 'Inactivas'],
            'datasets': [{
                'data': [activas - por_vencer, por_vencer, inactivas],
                'backgroundColor': ['#00ff88', '#ffaa00', '#ff4444'],
                'borderColor': ['#00ff88', '#ffaa00', '#ff4444'],
                'borderWidth': 2
            }]
        }
        
    elif chart_type == 'tendencias':
        # Tendencias de registros por semana
        ahora = timezone.now()
        semanas_data = []
        labels = []
        
        for i in range(8):
            inicio_semana = ahora - timedelta(weeks=i+1)
            fin_semana = ahora - timedelta(weeks=i)
            nuevos_semana = Empresa.objects.filter(
                fecha_inicio__gte=inicio_semana,
                fecha_inicio__lt=fin_semana
            ).count()
            semanas_data.append(nuevos_semana)
            labels.append(f'S-{i+1}')
        
        semanas_data.reverse()
        labels.reverse()
        
        data = {
            'labels': labels,
            'datasets': [{
                'label': 'Nuevos suscriptores',
                'data': semanas_data,
                'borderColor': '#00f5ff',
                'backgroundColor': 'rgba(0, 245, 255, 0.1)',
                'borderWidth': 3,
                'fill': True,
                'tension': 0.4
            }]
        }
    
    else:
        data = {'error': 'Tipo de gráfico no válido'}
    
    return JsonResponse(data)


@login_required
@user_passes_test(es_staff_o_admin)
def exportar_suscriptores_csv(request):
    """
    Exporta la lista completa de suscriptores a CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suscriptores_egarage.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Usuario', 'Email', 'Nombre Taller', 'País', 'Plan', 
        'Fecha Inicio', 'Fecha Fin', 'Días Restantes', 'Estado', 
        'Zona Horaria', 'Teléfono', 'Dirección'
    ])
    
    empresas = Empresa.objects.select_related('user').all()
    
    for empresa in empresas:
        writer.writerow([
            empresa.id,
            empresa.user.username,
            empresa.user.email,
            empresa.nombre_taller,
            empresa.get_pais_display(),
            empresa.get_plan_display(),
            empresa.fecha_inicio.strftime('%Y-%m-%d') if empresa.fecha_inicio else '',
            empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else '',
            empresa.dias_restantes,
            'Activa' if empresa.suscripcion_activa else 'Inactiva',
            empresa.zona_horaria,
            empresa.telefono,
            empresa.direccion
        ])
    
    return response


@login_required
@user_passes_test(es_staff_o_admin)
def detalle_suscriptor(request, empresa_id):
    """
    Vista detallada de un suscriptor específico
    """
    try:
        empresa = Empresa.objects.select_related('user').get(id=empresa_id)
        
        # Obtener comprobantes de pago
        comprobantes = ComprobantePago.objects.filter(empresa=empresa).order_by('-fecha_subida')[:5]
        
        # Calcular estadísticas de la empresa
        ahora = timezone.now()
        
        # Información adicional
        info_adicional = {
            'ultimo_login': empresa.user.last_login,
            'fecha_registro': empresa.user.date_joined,
            'es_staff': empresa.user.is_staff,
            'comprobantes_recientes': comprobantes,
            'dias_desde_registro': (ahora.date() - empresa.user.date_joined.date()).days if empresa.user.date_joined else 0,
        }
        
        context = {
            'empresa': empresa,
            'info_adicional': info_adicional,
        }
        
        return render(request, 'analytics/detalle_suscriptor.html', context)
        
    except Empresa.DoesNotExist:
        return JsonResponse({'error': 'Suscriptor no encontrado'}, status=404)

@login_required
def dashboard_avanzado(request):
    """
    Vista para el dashboard avanzado con funcionalidades adicionales
    URL: /analytics/admin/dashboard/avanzado/
    """
    # Verificar permisos de administrador
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('analytics:dashboard_ai')
    
    return render(request, 'analytics/dashboard_avanzado.html', {
        'titulo': 'Dashboard Avanzado',
        'usuario_admin': request.user,
        'timestamp': timezone.now()
    })

@login_required
def test_info_view(request):
    """
    Vista temporal para mostrar información de usuarios de prueba
    URL: /admin/test/info/
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('/')
    
    # Obtener usuarios de prueba
    usuarios_prueba = User.objects.filter(
        email__in=[
            'test_chile@egarage.cl',
            'test_chile_pago@egarage.cl', 
            'test_usa@egarage.com',
            'test_usa_pago@egarage.com'
        ]
    ).select_related('empresa')
    
    context = {
        'usuarios_prueba': usuarios_prueba,
        'timestamp': timezone.now()
    }
    
    return render(request, 'admin/test_info.html', context)

@login_required
def dashboard_avanzado(request):
    """
    Vista para el dashboard avanzado con funcionalidades adicionales
    URL: /analytics/admin/dashboard/avanzado/
    """
    # Verificar permisos de administrador
    if not es_staff_o_admin(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('analytics:dashboard_ai')
    
    return render(request, 'analytics/dashboard_avanzado.html', {
        'titulo': 'Dashboard Avanzado',
        'usuario_admin': request.user,
        'timestamp': timezone.now()
    })
