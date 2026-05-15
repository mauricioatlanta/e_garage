from django.urls import include, path

# Redirigir a las nuevas rutas unificadas
urlpatterns = [
    path("", include("taller.autocomplete.urls")),
]
