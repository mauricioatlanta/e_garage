from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('autocomplete/', include('taller.autocomplete.urls', namespace='autocomplete')),
    path('vehiculos/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),

    # Rutas principales de tu sistema
    path('', include('taller.urls')),
    path('taller/', include('taller.urls')),
]
