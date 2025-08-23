from django.urls import path
from .views_extra.views_configuracion import configuracion_tecnicos, configuracion_empresa

# URLconf para configuración
urlpatterns = [
    path('', configuracion_empresa, name='configuracion_principal'),
    path('empresa/', configuracion_empresa, name='configuracion_empresa'),
    path('tecnicos/', configuracion_tecnicos, name='configuracion_tecnicos'),
]
