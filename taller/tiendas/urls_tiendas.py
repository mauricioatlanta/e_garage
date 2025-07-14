# taller/urls/tiendas_urls.py

from django.urls import path
from taller.views.tiendas import crear_tienda

app_name = 'tiendas'

urlpatterns = [
    path('crear/', crear_tienda, name='crear_tienda'),
]
