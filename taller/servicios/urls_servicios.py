from django.urls import path
from taller.servicios.servicios import (
    explorador_servicios, crear_servicio, editar_servicio, eliminar_servicio, lista_servicios
)
from rest_framework.routers import DefaultRouter
from .views import ServicioViewSet, CategoriaServicioViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaServicioViewSet, basename='categorias')
router.register(r'servicios', ServicioViewSet, basename='servicios')

app_name = "servicios"

urlpatterns = [
    path('servicios/nuevo/', crear_servicio, name='formulario_servicio'),
    path('', explorador_servicios, name='explorador_servicios'),
    path('crear/', crear_servicio, name='crear_servicio'),
    path('editar/<int:servicio_id>/', editar_servicio, name='editar_servicio'),
    path('eliminar/<int:servicio_id>/', eliminar_servicio, name='eliminar_servicio'),
    path('lista/', lista_servicios, name='lista_servicios'),
]

urlpatterns += router.urls
