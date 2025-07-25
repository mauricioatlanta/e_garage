from django.urls import path
from .views.views_configuracion import configuracion_mecanicos, configuracion_empresa

# URLconf para configuración
urlpatterns = [
    path('', configuracion_empresa, name='configuracion_principal'),
    path('empresa/', configuracion_empresa, name='configuracion_empresa'),
    path('mecanicos/', configuracion_mecanicos, name='configuracion_mecanicos'),
]
