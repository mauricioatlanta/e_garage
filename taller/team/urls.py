"""
URLs para gestión de equipo (Team Management)
"""

from django.urls import path

from taller.views.team_views import (
    TeamListView,
    TeamCreateView,
    TeamUpdateView,
    TeamDeleteView,
    TeamReactivateView,
)

app_name = "team"

urlpatterns = [
    path("", TeamListView.as_view(), name="team_list"),
    path("crear/", TeamCreateView.as_view(), name="team_create"),
    path("editar/<int:pk>/", TeamUpdateView.as_view(), name="team_update"),
    path("desactivar/<int:pk>/", TeamDeleteView.as_view(), name="team_delete"),
    path("reactivar/<int:pk>/", TeamReactivateView.as_view(), name="team_reactivate"),
]
