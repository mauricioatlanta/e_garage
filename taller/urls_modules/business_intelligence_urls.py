"""
URLs para el módulo de inteligencia de negocio
"""
from django.urls import path
from taller.views import business_intelligence

app_name = 'business_intelligence'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', business_intelligence.dashboard_business_intelligence, name='dashboard'),
    
    # APIs para datos en tiempo real
    path('api/servicios-ranking/', business_intelligence.api_servicios_ranking, name='api_servicios_ranking'),
    path('api/repuestos-utilidad/', business_intelligence.api_repuestos_utilidad, name='api_repuestos_utilidad'),
    path('api/mecanicos-stats/', business_intelligence.api_mecanicos_stats, name='api_mecanicos_stats'),
]
