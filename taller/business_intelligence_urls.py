"""
URLs para el módulo de inteligencia de negocio
"""

from django.urls import path

from taller.views_extra import business_intelligence

app_name = "business_intelligence"

urlpatterns = [
    # Dashboard principal
    path(
        "dashboard/",
        business_intelligence.dashboard_business_intelligence,
        name="dashboard",
    ),
    # APIs para datos en tiempo real
    path(
        "api/servicios-ranking/",
        business_intelligence.api_servicios_ranking,
        name="api_servicios_ranking",
    ),
    path(
        "api/repuestos-utilidad/",
        business_intelligence.api_repuestos_utilidad,
        name="api_repuestos_utilidad",
    ),
    path(
        "api/tecnicos-stats/",
        business_intelligence.api_tecnicos_stats,
        name="api_tecnicos_stats",
    ),
]
