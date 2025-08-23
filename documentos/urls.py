from django.urls import path
from . import views

app_name = "documentos_legacy"

urlpatterns = [
    path('lista/', views.lista_documentos, name='lista_documentos'),
]
