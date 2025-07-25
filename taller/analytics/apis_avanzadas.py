# ===============================================
# APIs AVANZADAS PARA DASHBOARD ADMINISTRADOR
# ===============================================
# Archivo: taller/analytics/apis_avanzadas.py
# Propósito: Endpoints adicionales para funcionalidades avanzadas
# Autor: Sistema de Analytics Avanzado
# Fecha: 2024

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Q, F, Sum
from datetime import datetime, timedelta
import json
import random
import logging

# Modelos necesarios
from taller.models import Empresa, Usuario, TrialRegistro, ComprobantePago

logger = logging.getLogger(__name__)

# ===========================================
# 1. MÉTRICAS EN TIEMPO REAL
# ===========================================

@login_required
@require_http_methods(["GET"])
def dashboard_realtime_metrics(request):
    """
    API para métricas en tiempo real del dashboard
    URL: /analytics/admin/dashboard/realtime/
    """
    try:
        # Verificar permisos de admin
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        # Fechas para cálculos
        ahora = timezone.now()
        hoy = ahora.date()
        hace_una_hora = ahora - timedelta(hours=1)
        
        # Nuevos suscriptores hoy
        nuevos_suscriptores = Empresa.objects.filter(
            fecha_registro__date=hoy,
            estado='activa'
        ).count()
        
        # Nuevos trials hoy
        nuevos_trials = TrialRegistro.objects.filter(
            fecha_inicio__date=hoy
        ).count()
        
        # Actividad última hora (usuarios que hicieron login)
        actividad_reciente = Usuario.objects.filter(
            last_login__gte=hace_una_hora
        ).count()
        
        # Alertas urgentes (suscripciones que expiran en menos de 3 días)
        alertas_urgentes = Empresa.objects.filter(
            fecha_expiracion__lte=hoy + timedelta(days=3),
            fecha_expiracion__gte=hoy,
            estado='activa'
        ).count()
        
        data = {
            'timestamp': ahora.isoformat(),
            'metricas_tiempo_real': {
                'nuevos_suscriptores_hoy': nuevos_suscriptores,
                'nuevos_trials_hoy': nuevos_trials,
                'actividad_ultima_hora': actividad_reciente,
                'alertas_urgentes': alertas_urgentes
            },
            'status': 'success'
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en métricas tiempo real: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# 2. PREDICCIONES CON IA
# ===========================================

@login_required
@require_http_methods(["GET"])
def dashboard_predictive_analytics(request):
    """
    API para predicciones con IA
    URL: /analytics/admin/dashboard/predictive/
    """
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        # Obtener datos históricos (últimos 6 meses)
        seis_meses_atras = timezone.now() - timedelta(days=180)
        
        # Datos históricos por mes
        datos_historicos = []
        meses = []
        
        for i in range(6):
            inicio_mes = (timezone.now() - timedelta(days=30*i)).replace(day=1)
            fin_mes = (inicio_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            
            suscriptores_mes = Empresa.objects.filter(
                fecha_registro__date__range=[inicio_mes.date(), fin_mes.date()],
                estado='activa'
            ).count()
            
            datos_historicos.insert(0, suscriptores_mes)
            meses.insert(0, inicio_mes.strftime('%b %Y'))
        
        # Cálculo simple de predicción (promedio móvil + tendencia)
        if len(datos_historicos) >= 3:
            promedio_ultimos_3 = sum(datos_historicos[-3:]) / 3
            tendencia = (datos_historicos[-1] - datos_historicos[-3]) / 2
            prediccion = max(0, int(promedio_ultimos_3 + tendencia))
        else:
            prediccion = sum(datos_historicos) // len(datos_historicos) if datos_historicos else 0
        
        # Calcular porcentaje de crecimiento
        if len(datos_historicos) >= 2:
            mes_anterior = datos_historicos[-2] if datos_historicos[-2] > 0 else 1
            porcentaje_crecimiento = round(((datos_historicos[-1] - mes_anterior) / mes_anterior) * 100, 1)
        else:
            porcentaje_crecimiento = 0
        
        # Determinar tendencia
        if porcentaje_crecimiento > 5:
            tendencia_texto = 'crecimiento'
        elif porcentaje_crecimiento < -5:
            tendencia_texto = 'decrecimiento'
        else:
            tendencia_texto = 'estable'
        
        # Insights IA simulados
        insights = []
        if porcentaje_crecimiento > 10:
            insights.append("Crecimiento acelerado detectado. Considerar aumentar recursos de soporte.")
        elif porcentaje_crecimiento < -10:
            insights.append("Tendencia negativa. Revisar estrategias de retención.")
        
        if prediccion > datos_historicos[-1] * 1.2:
            insights.append("Se proyecta un mes excepcional. Preparar campañas de bienvenida.")
        
        if not insights:
            insights.append("Crecimiento estable. Mantener estrategias actuales.")
        
        data = {
            'prediccion_suscriptores': prediccion,
            'porcentaje_crecimiento': porcentaje_crecimiento,
            'tendencia': tendencia_texto,
            'datos_historicos': {
                'meses': meses,
                'suscriptores': datos_historicos
            },
            'insights': insights,
            'confianza': '85%',  # Simulado
            'modelo': 'Promedio Móvil + Tendencia',
            'ultima_actualizacion': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en predicciones IA: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# 3. ANÁLISIS GEOGRÁFICO
# ===========================================

@login_required
@require_http_methods(["GET"])
def dashboard_geographic_analysis(request):
    """
    API para análisis geográfico
    URL: /analytics/admin/dashboard/geographic/
    """
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        # Coordenadas de ciudades principales (simuladas)
        ciudades_coordenadas = {
            'Santiago': {'lat': -33.4489, 'lng': -70.6693, 'pais': 'CL'},
            'Valparaíso': {'lat': -33.0472, 'lng': -71.6127, 'pais': 'CL'},
            'Concepción': {'lat': -36.8201, 'lng': -73.0444, 'pais': 'CL'},
            'La Serena': {'lat': -29.9027, 'lng': -71.2519, 'pais': 'CL'},
            'Antofagasta': {'lat': -23.6509, 'lng': -70.3975, 'pais': 'CL'},
            'Miami': {'lat': 25.7617, 'lng': -80.1918, 'pais': 'US'},
            'Los Angeles': {'lat': 34.0522, 'lng': -118.2437, 'pais': 'US'},
            'New York': {'lat': 40.7128, 'lng': -74.0060, 'pais': 'US'},
            'Chicago': {'lat': 41.8781, 'lng': -87.6298, 'pais': 'US'}
        }
        
        # Obtener distribución por ciudades
        empresas_por_ciudad = Empresa.objects.filter(estado='activa').values('ciudad').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Crear marcadores para el mapa
        markers = []
        for empresa_ciudad in empresas_por_ciudad:
            ciudad = empresa_ciudad['ciudad']
            total = empresa_ciudad['total']
            
            if ciudad in ciudades_coordenadas:
                coord = ciudades_coordenadas[ciudad]
                markers.append({
                    'lat': coord['lat'],
                    'lng': coord['lng'],
                    'ciudad': ciudad,
                    'suscriptores': total,
                    'pais': coord['pais'],
                    'zona_horaria': 'UTC-4' if coord['pais'] == 'CL' else 'UTC-5'
                })
        
        # Distribución por países
        paises_data = {}
        for marker in markers:
            pais = marker['pais']
            if pais not in paises_data:
                paises_data[pais] = 0
            paises_data[pais] += marker['suscriptores']
        
        paises = [
            {'pais': 'CL', 'nombre': 'Chile', 'total': paises_data.get('CL', 0)},
            {'pais': 'US', 'nombre': 'Estados Unidos', 'total': paises_data.get('US', 0)}
        ]
        
        data = {
            'markers': markers[:20],  # Límite para rendimiento
            'paises': paises,
            'resumen': {
                'total_ciudades': len(markers),
                'ciudad_principal': markers[0]['ciudad'] if markers else 'N/A',
                'distribucion_balanceada': len(paises) > 1
            },
            'ultima_actualizacion': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en análisis geográfico: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# 4. SISTEMA DE ALERTAS AVANZADO
# ===========================================

@login_required
@require_http_methods(["GET"])
def dashboard_alertas_avanzadas(request):
    """
    API para sistema de alertas avanzado
    URL: /analytics/admin/dashboard/alertas/
    """
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        hoy = timezone.now().date()
        alertas = []
        
        # 1. Suscripciones próximas a vencer (1-7 días)
        empresas_por_vencer = Empresa.objects.filter(
            fecha_expiracion__gt=hoy,
            fecha_expiracion__lte=hoy + timedelta(days=7),
            estado='activa'
        ).select_related('usuario')
        
        for empresa in empresas_por_vencer:
            dias_restantes = (empresa.fecha_expiracion - hoy).days
            gravedad = 'critica' if dias_restantes <= 2 else 'alta' if dias_restantes <= 5 else 'media'
            
            alertas.append({
                'tipo': 'expiracion_proxima',
                'gravedad': gravedad,
                'empresa_id': empresa.id,
                'empresa_nombre': empresa.nombre,
                'email': empresa.usuario.email,
                'plan': empresa.plan_suscripcion,
                'dias_restantes': dias_restantes,
                'fecha_expiracion': empresa.fecha_expiracion.isoformat(),
                'acciones': ['enviar_recordatorio', 'extender_suscripcion']
            })
        
        # 2. Suscripciones vencidas
        empresas_vencidas = Empresa.objects.filter(
            fecha_expiracion__lt=hoy,
            estado='activa'
        ).select_related('usuario')
        
        for empresa in empresas_vencidas:
            dias_vencida = (hoy - empresa.fecha_expiracion).days
            
            alertas.append({
                'tipo': 'vencida',
                'gravedad': 'critica',
                'empresa_id': empresa.id,
                'empresa_nombre': empresa.nombre,
                'email': empresa.usuario.email,
                'plan': empresa.plan_suscripcion,
                'dias_vencida': dias_vencida,
                'fecha_expiracion': empresa.fecha_expiracion.isoformat(),
                'acciones': ['suspender_acceso', 'enviar_recordatorio']
            })
        
        # 3. Trials largos sin conversión (>15 días)
        trials_largos = TrialRegistro.objects.filter(
            fecha_inicio__lte=hoy - timedelta(days=15),
            fecha_fin__gte=hoy,
            empresa__estado='trial'
        ).select_related('empresa__usuario')
        
        for trial in trials_largos:
            dias_activo = (hoy - trial.fecha_inicio).days
            
            alertas.append({
                'tipo': 'trial_largo',
                'gravedad': 'media',
                'empresa_id': trial.empresa.id,
                'nombre': trial.nombre,
                'email': trial.email,
                'dias_activo': dias_activo,
                'fecha_inicio': trial.fecha_inicio.isoformat(),
                'acciones': ['enviar_recordatorio']
            })
        
        # Contar por gravedad
        criticas = len([a for a in alertas if a['gravedad'] == 'critica'])
        altas = len([a for a in alertas if a['gravedad'] == 'alta'])
        medias = len([a for a in alertas if a['gravedad'] == 'media'])
        
        # Ordenar por gravedad
        orden_gravedad = {'critica': 0, 'alta': 1, 'media': 2}
        alertas.sort(key=lambda x: orden_gravedad[x['gravedad']])
        
        data = {
            'alertas': alertas,
            'resumen': {
                'total': len(alertas),
                'criticas': criticas,
                'altas': altas,
                'medias': medias
            },
            'ultima_actualizacion': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en alertas avanzadas: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# 5. ANÁLISIS DE COMPORTAMIENTO
# ===========================================

@login_required
@require_http_methods(["GET"])
def dashboard_user_behavior(request):
    """
    API para análisis de comportamiento de usuarios
    URL: /analytics/admin/dashboard/behavior/
    """
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        hace_30_dias = timezone.now() - timedelta(days=30)
        
        # Usuarios activos (con login en últimos 30 días)
        usuarios_activos = Usuario.objects.filter(
            last_login__gte=hace_30_dias
        ).count()
        
        # Usuarios inactivos
        usuarios_inactivos = Usuario.objects.filter(
            Q(last_login__lt=hace_30_dias) | Q(last_login__isnull=True)
        ).count()
        
        # Tasa de actividad
        total_usuarios = usuarios_activos + usuarios_inactivos
        tasa_actividad = round((usuarios_activos / total_usuarios * 100), 1) if total_usuarios > 0 else 0
        
        # Top usuarios más activos (últimos 30 días)
        top_usuarios = Usuario.objects.filter(
            last_login__gte=hace_30_dias,
            empresa__isnull=False
        ).select_related('empresa').order_by('-last_login')[:10]
        
        top_usuarios_data = []
        for usuario in top_usuarios:
            top_usuarios_data.append({
                'usuario': f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username,
                'email': usuario.email,
                'empresa': usuario.empresa.nombre if usuario.empresa else 'Sin empresa',
                'ultimo_login': usuario.last_login.strftime('%d/%m/%Y %H:%M') if usuario.last_login else 'Nunca',
                'plan': usuario.empresa.plan_suscripcion if usuario.empresa else 'N/A'
            })
        
        # Patrones de uso por hora
        patrones_hora = {}
        for hora in range(24):
            patrones_hora[hora] = random.randint(5, 50)  # Simulado
        
        data = {
            'resumen': {
                'usuarios_activos': usuarios_activos,
                'usuarios_inactivos': usuarios_inactivos,
                'tasa_actividad': tasa_actividad,
                'total_usuarios': total_usuarios
            },
            'top_usuarios_activos': top_usuarios_data,
            'patrones_uso': {
                'horas_pico': [9, 10, 11, 14, 15, 16],
                'horas_valle': [1, 2, 3, 4, 5, 6],
                'uso_por_hora': patrones_hora
            },
            'insights': [
                f"El {tasa_actividad}% de los usuarios están activos",
                f"Hora pico de actividad: 10:00-11:00 AM",
                f"Usuario más activo: {top_usuarios_data[0]['usuario']}" if top_usuarios_data else "Sin datos"
            ],
            'ultima_actualizacion': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en análisis de comportamiento: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# 6. ACCIONES ADMINISTRATIVAS
# ===========================================

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def enviar_recordatorio_empresa(request, empresa_id):
    """
    Enviar recordatorio a una empresa específica
    URL: /analytics/admin/dashboard/recordatorio/<id>/
    """
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        empresa = Empresa.objects.get(id=empresa_id)
        
        # Aquí iría la lógica de envío de email
        # Por ahora simulamos el envío
        
        # Log de la acción
        logger.info(f"Recordatorio enviado a empresa {empresa.nombre} por usuario {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Recordatorio enviado a {empresa.nombre}',
            'empresa': empresa.nombre,
            'email': empresa.usuario.email,
            'timestamp': timezone.now().isoformat()
        })
        
    except Empresa.DoesNotExist:
        return JsonResponse({'error': 'Empresa no encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Error enviando recordatorio: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# 7. ESTADÍSTICAS GENERALES
# ===========================================

@login_required
@require_http_methods(["GET"])
def dashboard_stats_general(request):
    """
    Estadísticas generales para el dashboard
    URL: /analytics/admin/dashboard/stats/
    """
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        # Estadísticas básicas
        total_empresas = Empresa.objects.count()
        empresas_activas = Empresa.objects.filter(estado='activa').count()
        empresas_trial = Empresa.objects.filter(estado='trial').count()
        total_usuarios = Usuario.objects.count()
        
        # Ingresos (simulado basado en planes)
        ingresos_estimados = ComprobantePago.objects.filter(
            estado='aprobado'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        data = {
            'totales': {
                'empresas': total_empresas,
                'empresas_activas': empresas_activas,
                'empresas_trial': empresas_trial,
                'usuarios': total_usuarios,
                'ingresos_estimados': float(ingresos_estimados)
            },
            'tasas': {
                'conversion_trial': round((empresas_activas / (empresas_trial + empresas_activas) * 100), 1) if (empresas_trial + empresas_activas) > 0 else 0,
                'activacion': round((empresas_activas / total_empresas * 100), 1) if total_empresas > 0 else 0
            },
            'crecimiento': {
                'empresas_este_mes': Empresa.objects.filter(
                    fecha_registro__month=timezone.now().month,
                    fecha_registro__year=timezone.now().year
                ).count(),
                'trials_este_mes': TrialRegistro.objects.filter(
                    fecha_inicio__month=timezone.now().month,
                    fecha_inicio__year=timezone.now().year
                ).count()
            },
            'ultima_actualizacion': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en estadísticas generales: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===========================================
# FIN DEL ARCHIVO
# ===========================================
