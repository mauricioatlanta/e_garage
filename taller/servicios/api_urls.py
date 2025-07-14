
from rest_framework.routers import DefaultRouter
from .api_views import CategoriaServicioViewSet, SubcategoriaServicioViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaServicioViewSet)
router.register(r'subcategorias', SubcategoriaServicioViewSet)

urlpatterns = router.urls
