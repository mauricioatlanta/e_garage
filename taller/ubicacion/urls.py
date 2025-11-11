"""
URLs para la API de ubicaciones

Patrón:
  /api/locations?country=XX        → estados/departamentos
  /api/locations?country=XX&state=YY → ciudades
"""

from django.urls import path

from .api import cities_by_state, locations, states_by_country

app_name = "ubicacion_api"

urlpatterns = [
    # API unificada (query params)
    path("locations", locations, name="locations"),
    # APIs alternativas (path params)
    path("locations/states/<str:country_code>/", states_by_country, name="states_by_country"),
    path("locations/cities/<int:state_id>/", cities_by_state, name="cities_by_state"),
]
