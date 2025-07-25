
from rest_framework.routers import DefaultRouter
from .api_views import CategoriaServicioViewSet, SubcategoriaServicioViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaServicioViewSet, basename='categorias')
router.register(r'subcategorias', SubcategoriaServicioViewSet, basename='subcategorias')

urlpatterns = router.urls
