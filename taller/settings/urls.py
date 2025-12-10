from django.urls import path

from ..views_extra.company_settings_views import company_settings_view
from ..views_extra.configuracion_servicios_views import configurar_servicios

app_name = "settings"

urlpatterns = [
    path("", company_settings_view, name="ver_configuracion"),
    path("editar/", company_settings_view, name="ajustar_configuracion"),
    path("servicios/", configurar_servicios, name="configurar_servicios"),
]
