from django.urls import path
from taller.views import obtener_ciudades_por_region

urlpatterns = [
    path('obtener-ciudades/', obtener_ciudades_por_region, name='obtener_ciudades'),
]
