# -*- coding: utf-8 -*-
"""
URLs para la API de ubicaciones

Patrón:
  /api/locations?country=XX        → estados/departamentos
  /api/locations?country=XX&state=YY → ciudades
  /api/locations/states/?country=XX → estados por país
  /api/locations/cities/?state_id=XX → ciudades por estado
"""
from django.urls import path

from . import api
from . import views

app_name = "ubicacion"

urlpatterns = [
    # (Opcional) formulario legacy /registro/
    path("registro/", views.registro_ubicacion, name="registro"),
    
    # ✅ API nueva (unificada multi-país)
    path("api/locations/", api.locations, name="locations_api"),
    
    # ✅ API de estados (soporta query param y path param)
    path("api/locations/states/", api.states_by_country, name="states_by_country"),
    path("api/locations/states/<str:country_code>/", api.states_by_country, name="states_by_country_path"),
    
    # ✅ API de ciudades (soporta query param y path param)
    path("api/locations/cities/", api.cities_by_state, name="cities_by_state"),
    path("api/locations/cities/<int:state_id>/", api.cities_by_state, name="cities_by_state_path"),
]
