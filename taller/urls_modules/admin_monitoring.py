"""
URLs para el panel administrativo de monitoreo de suscripciones
"""

from django.urls import path
from taller.views import admin_monitoring

app_name = 'admin_monitoring'

urlpatterns = [
    # Dashboard principal
    path('', admin_monitoring.subscription_dashboard, name='subscription_dashboard'),
    
    # Lista de suscripciones con filtros
    path('list/', admin_monitoring.subscription_list, name='subscription_list'),
    
    # Analytics avanzados
    path('analytics/', admin_monitoring.subscription_analytics, name='subscription_analytics'),
    
    # Detalle de suscripción específica
    path('<int:empresa_id>/', admin_monitoring.subscription_detail, name='subscription_detail'),
    
    # Acciones administrativas
    path('<int:empresa_id>/actions/', admin_monitoring.subscription_actions, name='subscription_actions'),
    
    # Exportación de datos
    path('export/', admin_monitoring.export_subscriptions, name='export_subscriptions'),
    
    # API para estadísticas en tiempo real
    path('api/stats/', admin_monitoring.subscription_api_stats, name='subscription_api_stats'),
]
