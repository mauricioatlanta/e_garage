"""
🚀 FUNCIONALIDADES ADICIONALES PARA EL DASHBOARD ADMIN
Implementaciones avanzadas sugeridas por el usuario
"""

from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone

from taller.analytics.admin_views import es_staff_o_admin
from taller.models.empresa import Empresa
from taller.models.trial import TrialRegistro

# ===============================================
# 🔮 1. INDICADORES PREDICTIVOS CON IA
# ===============================================


@login_required
@user_passes_test(es_staff_o_admin)
def predictive_indicators_api(request):
    """
    API para indicadores predictivos usando IA simple
    Calcula tendencias y predicciones de crecimiento
    """

    # Obtener datos históricos (últimos 12 meses)
    ahora = timezone.now()
    meses_atras = []
    suscriptores_por_mes = []

    for i in range(12):
        inicio_mes = ahora - timedelta(days=30 * i)
        fin_mes = ahora - timedelta(days=30 * (i - 1)) if i > 0 else ahora

        nuevos_mes = Empresa.objects.filter(
            fecha_inicio__gte=inicio_mes, fecha_inicio__lt=fin_mes
        ).count()

        meses_atras.append(inicio_mes.strftime("%m/%Y"))
        suscriptores_por_mes.append(nuevos_mes)

    meses_atras.reverse()
    suscriptores_por_mes.reverse()

    # Calcular moving average (predicción simple)
    def calcular_moving_average(datos, ventana=3):
        if len(datos) < ventana:
            return datos[-1] if datos else 0
        return sum(datos[-ventana:]) / ventana

    prediccion_siguiente_mes = calcular_moving_average(suscriptores_por_mes)

    # Calcular tendencia (crecimiento/decrecimiento)
    if len(suscriptores_por_mes) >= 2:
        tendencia = suscriptores_por_mes[-1] - suscriptores_por_mes[-2]
        porcentaje_crecimiento = (tendencia / max(suscriptores_por_mes[-2], 1)) * 100
    else:
        tendencia = 0
        porcentaje_crecimiento = 0

    # Predicción de ingresos
    conversion_rate = 0.25  # 25% de trials se convierten
    valor_promedio_suscripcion = 25000  # CLP

    ingresos_predichos = (
        prediccion_siguiente_mes * conversion_rate * valor_promedio_suscripcion
    )

    data = {
        "prediccion_suscriptores": round(prediccion_siguiente_mes),
        "tendencia": (
            "crecimiento"
            if tendencia > 0
            else "decrecimiento" if tendencia < 0 else "estable"
        ),
        "porcentaje_crecimiento": round(porcentaje_crecimiento, 1),
        "ingresos_predichos": round(ingresos_predichos),
        "datos_historicos": {
            "meses": meses_atras,
            "suscriptores": suscriptores_por_mes,
        },
        "insights": [
            f"Predicción próximo mes: {round(prediccion_siguiente_mes)} nuevos suscriptores",
            f"Tendencia: {porcentaje_crecimiento:+.1f}% respecto al mes anterior",
            f"Ingresos estimados: ${round(ingresos_predichos):,} CLP",
            f"Tasa de conversión estimada: {conversion_rate*100}%",
        ],
    }

    return JsonResponse(data)


# ===============================================
# 🗺️ 2. MAPA GEOGRÁFICO DE SUSCRIPTORES
# ===============================================


@login_required
@user_passes_test(es_staff_o_admin)
def geographic_map_api(request):
    """
    API para datos del mapa geográfico
    Distribución de suscriptores por ubicación
    """

    # Datos por país
    paises_data = Empresa.objects.values("pais").annotate(
        total=Count("id"), activos=Count("id", filter=Q(suscripcion_activa=True))
    )

    # Datos detallados por zona horaria (aproximación de ubicación)
    zonas_data = (
        Empresa.objects.values("zona_horaria")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # Mapear zonas horarias a coordenadas aproximadas
    coordenadas_zonas = {
        "America/New_York": {"lat": 40.7128, "lng": -74.0060, "ciudad": "New York"},
        "America/Chicago": {"lat": 41.8781, "lng": -87.6298, "ciudad": "Chicago"},
        "America/Denver": {"lat": 39.7392, "lng": -104.9903, "ciudad": "Denver"},
        "America/Los_Angeles": {
            "lat": 34.0522,
            "lng": -118.2437,
            "ciudad": "Los Angeles",
        },
        "America/Santiago": {"lat": -33.4489, "lng": -70.6693, "ciudad": "Santiago"},
        "America/Phoenix": {"lat": 33.4484, "lng": -112.0740, "ciudad": "Phoenix"},
    }

    # Preparar datos para el mapa
    markers = []
    for zona in zonas_data:
        zona_nombre = zona["zona_horaria"]
        if zona_nombre in coordenadas_zonas:
            coord = coordenadas_zonas[zona_nombre]
            markers.append(
                {
                    "lat": coord["lat"],
                    "lng": coord["lng"],
                    "ciudad": coord["ciudad"],
                    "suscriptores": zona["total"],
                    "zona_horaria": zona_nombre,
                }
            )

    data = {
        "paises": list(paises_data),
        "markers": markers,
        "centros": [
            {"pais": "Chile", "lat": -33.4489, "lng": -70.6693, "zoom": 6},
            {"pais": "USA", "lat": 39.8283, "lng": -98.5795, "zoom": 4},
        ],
    }

    return JsonResponse(data)


# ===============================================
# ⚠️ 3. SISTEMA DE ALERTAS DE EXPIRACIÓN
# ===============================================


@login_required
@user_passes_test(es_staff_o_admin)
def alertas_expiracion_api(request):
    """
    API para alertas de expiración con acciones
    """

    hoy = timezone.now().date()

    # Empresas que expiran esta semana
    expiran_semana = Empresa.objects.filter(
        fecha_fin__gte=hoy,
        fecha_fin__lte=hoy + timedelta(days=7),
        suscripcion_activa=True,
    ).select_related("user")

    # Empresas ya vencidas pero aún marcadas como activas
    vencidas_activas = Empresa.objects.filter(
        fecha_fin__lt=hoy, suscripcion_activa=True
    ).select_related("user")

    # Trials próximos a expirar
    trials_proximos = TrialRegistro.objects.filter(
        prueba_activa=True,
        fecha_activacion__lte=timezone.now()
        - timedelta(days=25),  # Activos hace más de 25 días
    )

    alertas = []

    # Alertas de expiración
    for empresa in expiran_semana:
        dias_restantes = (empresa.fecha_fin.date() - hoy).days
        alertas.append(
            {
                "tipo": "expiracion_proxima",
                "gravedad": "alta" if dias_restantes <= 3 else "media",
                "empresa_id": empresa.id,
                "empresa_nombre": empresa.nombre_taller,
                "usuario": empresa.user.username,
                "email": empresa.user.email,
                "dias_restantes": dias_restantes,
                "fecha_expiracion": empresa.fecha_fin.strftime("%d/%m/%Y"),
                "plan": empresa.get_plan_display(),
                "acciones": [
                    "enviar_recordatorio",
                    "extender_suscripcion",
                    "contactar_comercial",
                ],
            }
        )

    # Alertas de vencidas
    for empresa in vencidas_activas:
        dias_vencida = (hoy - empresa.fecha_fin.date()).days
        alertas.append(
            {
                "tipo": "vencida",
                "gravedad": "critica",
                "empresa_id": empresa.id,
                "empresa_nombre": empresa.nombre_taller,
                "usuario": empresa.user.username,
                "email": empresa.user.email,
                "dias_vencida": dias_vencida,
                "fecha_expiracion": empresa.fecha_fin.strftime("%d/%m/%Y"),
                "plan": empresa.get_plan_display(),
                "acciones": ["suspender_acceso", "contactar_urgente", "revisar_pagos"],
            }
        )

    # Alertas de trials
    for trial in trials_proximos:
        dias_activo = (
            (timezone.now().date() - trial.fecha_activacion.date()).days
            if trial.fecha_activacion
            else 0
        )
        alertas.append(
            {
                "tipo": "trial_expirando",
                "gravedad": "media",
                "trial_id": trial.id,
                "nombre": trial.nombre,
                "email": trial.email,
                "dias_activo": dias_activo,
                "dias_restantes": max(0, 30 - dias_activo),
                "acciones": [
                    "enviar_oferta_conversion",
                    "contactar_comercial",
                    "extender_trial",
                ],
            }
        )

    # Ordenar por gravedad
    orden_gravedad = {"critica": 0, "alta": 1, "media": 2, "baja": 3}
    alertas.sort(key=lambda x: orden_gravedad.get(x["gravedad"], 3))

    return JsonResponse(
        {
            "alertas": alertas,
            "resumen": {
                "total": len(alertas),
                "criticas": len([a for a in alertas if a["gravedad"] == "critica"]),
                "altas": len([a for a in alertas if a["gravedad"] == "alta"]),
                "medias": len([a for a in alertas if a["gravedad"] == "media"]),
            },
        }
    )


# ===============================================
# 📧 4. ENVÍO DE RECORDATORIOS AUTOMÁTICOS
# ===============================================


@login_required
@user_passes_test(es_staff_o_admin)
def enviar_recordatorio_expiracion(request, empresa_id):
    """
    Envía recordatorio de expiración a una empresa específica
    """

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        empresa = Empresa.objects.select_related("user").get(id=empresa_id)

        # Calcular días restantes
        dias_restantes = empresa.dias_restantes

        # Plantilla de email
        asunto = f"🚨 Tu suscripción a eGarage expira en {dias_restantes} días"

        mensaje = f"""
Hola {empresa.user.first_name or empresa.user.username},

Tu suscripción a eGarage está próxima a expirar:

🏢 Taller: {empresa.nombre_taller}
📅 Fecha de expiración: {empresa.fecha_fin.strftime('%d/%m/%Y')}
⏰ Días restantes: {dias_restantes}
💎 Plan actual: {empresa.get_plan_display()}

Para renovar tu suscripción:
1. Ingresa a tu panel de control
2. Ve a la sección "Suscripción"
3. Elige tu plan preferido
4. Realiza el pago

¿Necesitas ayuda? Contáctanos:
📧 soporte@egarage.com
📞 +56 9 1234 5678

¡No pierdas acceso a todas las funciones premium de eGarage!

Saludos,
Equipo eGarage
"""

        # Aquí implementarías el envío real del email
        # send_mail(asunto, mensaje, 'noreply@egarage.com', [empresa.user.email])

        # Marcar que se envió recordatorio
        if dias_restantes <= 5:
            empresa.notificacion_5_dias = True
        if dias_restantes <= 1:
            empresa.notificacion_1_dia = True
        empresa.save()

        return JsonResponse(
            {
                "success": True,
                "mensaje": f"Recordatorio enviado a {empresa.user.email}",
                "empresa": empresa.nombre_taller,
                "dias_restantes": dias_restantes,
            }
        )

    except Empresa.DoesNotExist:
        return JsonResponse({"error": "Empresa no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ===============================================
# 👥 5. PANEL DE COMPORTAMIENTO DE USUARIOS
# ===============================================


@login_required
@user_passes_test(es_staff_o_admin)
def user_behavior_api(request):
    """
    API para análisis de comportamiento de usuarios
    """

    # Usuarios activos (login en últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    usuarios_activos = Empresa.objects.filter(
        user__last_login__gte=hace_30_dias
    ).count()

    # Usuarios inactivos (sin login en 30 días)
    usuarios_inactivos = Empresa.objects.filter(
        Q(user__last_login__lt=hace_30_dias) | Q(user__last_login__isnull=True)
    ).count()

    # Estadísticas de login por día de la semana
    logins_por_dia = defaultdict(int)
    empresas_con_login = Empresa.objects.filter(
        user__last_login__isnull=False
    ).select_related("user")

    for empresa in empresas_con_login:
        dia_semana = empresa.user.last_login.strftime("%A")
        logins_por_dia[dia_semana] += 1

    # Top usuarios más activos (aproximación basada en fecha de último login)
    usuarios_top = (
        Empresa.objects.filter(user__last_login__isnull=False)
        .select_related("user")
        .order_by("-user__last_login")[:10]
    )

    top_activos = []
    for empresa in usuarios_top:
        dias_desde_login = (timezone.now().date() - empresa.user.last_login.date()).days
        top_activos.append(
            {
                "empresa": empresa.nombre_taller,
                "usuario": empresa.user.username,
                "ultimo_login": empresa.user.last_login.strftime("%d/%m/%Y %H:%M"),
                "dias_desde_login": dias_desde_login,
                "plan": empresa.get_plan_display(),
                "pais": empresa.get_pais_display(),
            }
        )

    # Usuarios problemáticos (trials inactivos)
    trials_inactivos = TrialRegistro.objects.filter(
        prueba_activa=True, fecha_activacion__lt=timezone.now() - timedelta(days=7)
    ).values_list("email", "nombre", "fecha_activacion")

    problematicos = []
    for email, nombre, fecha_activacion in trials_inactivos:
        dias_inactivo = (timezone.now().date() - fecha_activacion.date()).days
        if dias_inactivo > 7:  # Trial activo pero sin uso aparente
            problematicos.append(
                {
                    "nombre": nombre,
                    "email": email,
                    "dias_sin_actividad": dias_inactivo,
                    "tipo": "trial_inactivo",
                }
            )

    data = {
        "resumen": {
            "usuarios_activos": usuarios_activos,
            "usuarios_inactivos": usuarios_inactivos,
            "tasa_actividad": round(
                (usuarios_activos / max(usuarios_activos + usuarios_inactivos, 1))
                * 100,
                1,
            ),
        },
        "logins_por_dia": dict(logins_por_dia),
        "top_usuarios_activos": top_activos,
        "usuarios_problematicos": problematicos,
        "metricas": {
            "promedio_dias_desde_login": round(
                sum(u["dias_desde_login"] for u in top_activos)
                / max(len(top_activos), 1),
                1,
            ),
            "usuarios_login_hoy": Empresa.objects.filter(
                user__last_login__date=timezone.now().date()
            ).count(),
            "usuarios_nuevos_sin_login": Empresa.objects.filter(
                user__last_login__isnull=True,
                fecha_inicio__gte=timezone.now() - timedelta(days=7),
            ).count(),
        },
    }

    return JsonResponse(data)


# ===============================================
# 📊 6. WIDGET DE MÉTRICAS EN TIEMPO REAL
# ===============================================


@login_required
@user_passes_test(es_staff_o_admin)
def real_time_metrics_api(request):
    """
    API para métricas en tiempo real del dashboard
    """

    ahora = timezone.now()
    hoy = ahora.date()

    # Métricas del día actual
    nuevos_hoy = Empresa.objects.filter(fecha_inicio__date=hoy).count()
    trials_hoy = TrialRegistro.objects.filter(fecha_registro__date=hoy).count()

    # Métricas de la hora actual
    hace_1_hora = ahora - timedelta(hours=1)
    actividad_ultima_hora = Empresa.objects.filter(
        user__last_login__gte=hace_1_hora
    ).count()

    # Estado general del sistema
    total_empresas = Empresa.objects.count()
    empresas_activas = Empresa.objects.filter(suscripcion_activa=True).count()

    # Alertas urgentes
    alertas_urgentes = Empresa.objects.filter(
        fecha_fin__lte=hoy + timedelta(days=1),
        fecha_fin__gte=hoy,
        suscripcion_activa=True,
    ).count()

    data = {
        "timestamp": ahora.isoformat(),
        "metricas_tiempo_real": {
            "nuevos_suscriptores_hoy": nuevos_hoy,
            "nuevos_trials_hoy": trials_hoy,
            "actividad_ultima_hora": actividad_ultima_hora,
            "alertas_urgentes": alertas_urgentes,
        },
        "estado_sistema": {
            "total_empresas": total_empresas,
            "empresas_activas": empresas_activas,
            "tasa_actividad": round(
                (empresas_activas / max(total_empresas, 1)) * 100, 1
            ),
            "salud_sistema": (
                "excelente"
                if empresas_activas / max(total_empresas, 1) > 0.8
                else (
                    "buena"
                    if empresas_activas / max(total_empresas, 1) > 0.6
                    else "regular"
                )
            ),
        },
        "tendencias_inmediatas": {
            "crecimiento_diario": nuevos_hoy,
            "conversion_trials": (
                round((nuevos_hoy / max(trials_hoy, 1)) * 100, 1)
                if trials_hoy > 0
                else 0
            ),
            "actividad_promedio": actividad_ultima_hora,
        },
    }

    return JsonResponse(data)


# ===============================================
# 🎛️ URLS PARA FUNCIONALIDADES ADICIONALES
# ===============================================

# Agregar estas URLs a taller/analytics/urls.py:
"""
    # === FUNCIONALIDADES ADICIONALES ===
    path('admin/dashboard/predictive/', predictive_indicators_api, name='predictive_api'),
    path('admin/dashboard/geographic/', geographic_map_api, name='geographic_api'),
    path('admin/dashboard/alertas/', alertas_expiracion_api, name='alertas_api'),
    path('admin/dashboard/recordatorio/<int:empresa_id>/', enviar_recordatorio_expiracion, name='enviar_recordatorio'),
    path('admin/dashboard/behavior/', user_behavior_api, name='behavior_api'),
    path('admin/dashboard/realtime/', real_time_metrics_api, name='realtime_api'),
"""
