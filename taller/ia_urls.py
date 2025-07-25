from django.urls import path
from . import ia_views

app_name = 'ia'

urlpatterns = [
    # Vista principal de IA
    path('', ia_views.sugerencias_basicas_demo, name='sugerencias_basicas'),
    
    # API para sugerencias AJAX
    path('api/sugerencias/<str:marca>/', ia_views.obtener_sugerencias_vehiculo, name='api_sugerencias'),
    
    # Endpoints para el onboarding
    path('demo/vehiculo/', ia_views.demo_sugerencias_vehiculo, name='demo_vehiculo'),
]
