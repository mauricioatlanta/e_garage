from django.urls import path
from taller.api import views

app_name = "api"

urlpatterns = [
    path('status/', views.api_status, name='api_status'),
    path('tiendas/crear/', views.crear_tienda_api, name='crear_tienda_api'),
]
