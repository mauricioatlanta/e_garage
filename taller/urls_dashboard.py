from django.urls import path
from . import views_dashboard

urlpatterns = [
    path('ajax/vehiculo/', views_dashboard.registrar_vehiculo, name='ajax_registrar_vehiculo'),
    path('ajax/documento/', views_dashboard.registrar_documento, name='ajax_registrar_documento'),
    path('ajax/venta/', views_dashboard.registrar_venta, name='ajax_registrar_venta'),
]
