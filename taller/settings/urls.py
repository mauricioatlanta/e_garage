from django.urls import path
from ..views import settings as v

app_name = 'settings'

urlpatterns = [
    path('', v.ver_configuracion, name='ver_configuracion'),
    path('editar/', v.ajustar_configuracion, name='ajustar_configuracion'),
]
