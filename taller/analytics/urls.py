"""
URLs para el sistema de Analytics AI
Dashboard futurista con diferenciación por país
"""

from django.urls import path
from django.shortcuts import render
from . import views
from .admin_views import dashboard_admin, api_admin_charts, exportar_suscriptores_csv, detalle_suscriptor, test_info_view
from .funcionalidades_adicionales import (
    predictive_indicators_api, geographic_map_api, alertas_expiracion_api,
    enviar_recordatorio_expiracion, user_behavior_api, real_time_metrics_api
)
from . import apis_avanzadas
from . import admin_views

app_name = 'analytics'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_ai_view, name='dashboard'),
    path('dashboard/', views.dashboard_ai_view, name='dashboard_ai'),
    
    # APIs para gráficas en tiempo real
    path('revenue-api/', views.revenue_analytics_api, name='revenue_api'),
    path('vehicle-api/', views.vehicle_analytics_api, name='vehicle_api'),
    path('predictive-api/', views.predictive_analytics_api, name='predictive_api'),
    path('real-time/', views.real_time_metrics_api, name='real_time_api'),
    
    # === DASHBOARD ADMIN SUSCRIPTORES ===
    path('admin/dashboard/', dashboard_admin, name='dashboard_admin'),
    path('admin/dashboard/api/charts/', api_admin_charts, name='admin_charts_api'),
    path('admin/dashboard/exportar-csv/', exportar_suscriptores_csv, name='exportar_csv'),
    path('admin/dashboard/suscriptor/<int:empresa_id>/', detalle_suscriptor, name='detalle_suscriptor'),
    
    # === DASHBOARD AVANZADO ===
    path('admin/dashboard/avanzado/', admin_views.dashboard_avanzado, name='dashboard_avanzado'),
    
    # === FUNCIONALIDADES ADICIONALES ORIGINALES ===
    path('admin/dashboard/predictive/', predictive_indicators_api, name='predictive_api'),
    path('admin/dashboard/geographic/', geographic_map_api, name='geographic_api'),
    path('admin/dashboard/alertas/', alertas_expiracion_api, name='alertas_api'),
    path('admin/dashboard/recordatorio/<int:empresa_id>/', enviar_recordatorio_expiracion, name='enviar_recordatorio'),
    path('admin/dashboard/behavior/', user_behavior_api, name='behavior_api'),
    path('admin/dashboard/realtime/', real_time_metrics_api, name='realtime_api'),
    
    # === APIS AVANZADAS NUEVAS ===
    path('admin/dashboard/realtime-new/', apis_avanzadas.dashboard_realtime_metrics, name='api_realtime_new'),
    path('admin/dashboard/predictive-new/', apis_avanzadas.dashboard_predictive_analytics, name='api_predictive_new'),
    path('admin/dashboard/geographic-new/', apis_avanzadas.dashboard_geographic_analysis, name='api_geographic_new'),
    path('admin/dashboard/alertas-new/', apis_avanzadas.dashboard_alertas_avanzadas, name='api_alertas_new'),
    path('admin/dashboard/behavior-new/', apis_avanzadas.dashboard_user_behavior, name='api_behavior_new'),
    path('admin/dashboard/stats/', apis_avanzadas.dashboard_stats_general, name='api_stats'),
    path('admin/dashboard/recordatorio-new/<int:empresa_id>/', apis_avanzadas.enviar_recordatorio_empresa, name='enviar_recordatorio_new'),
    
    # === VISTA DE INFORMACIÓN DE PRUEBA ===
    path('admin/test/info/', admin_views.test_info_view, name='test_info'),
    
    # AI Insights
    path('ai-insights/', views.AIInsightView.as_view(), name='ai_insights'),
    
    # Exportación de reportes
    path('export/', views.export_report_view, name='export_report'),
]
