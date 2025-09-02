from django.urls import path
from . import ajax_views

app_name = 'vehiculos_ajax'

urlpatterns = [
    path('marcas/', ajax_views.ajax_marcas, name='ajax_marcas'),
    path('modelos/', ajax_views.ajax_modelos, name='ajax_modelos'),
    path('motores/', ajax_views.ajax_motores, name='ajax_motores'),
    path('cajas/', ajax_views.ajax_cajas, name='ajax_cajas'),
]
