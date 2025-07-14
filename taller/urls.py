from django.urls import path, include
from . import views

urlpatterns = [
    path('debug-autocomplete/', views.debug_cliente_autocomplete, name='debug_autocomplete'),
    path('autocomplete/', include('taller.autocomplete.urls', namespace='autocomplete')),
]
