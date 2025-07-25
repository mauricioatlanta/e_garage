from django.urls import path
from taller.api import views

app_name = "api"

urlpatterns = [
    path('status/', views.api_status, name='api_status'),
    path('tiendas/crear/', views.crear_tienda_api, name='crear_tienda_api'),
    path('clientes/', views.buscar_clientes_api, name='buscar_clientes_api'),
    path('modelos/', views.buscar_modelos_api, name='buscar_modelos_api'),
    path('motores/', views.buscar_motores_api, name='buscar_motores_api'),
    path('cajas/', views.buscar_cajas_api, name='buscar_cajas_api'),
]
