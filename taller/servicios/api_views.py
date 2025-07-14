
from rest_framework import viewsets
from .models import CategoriaServicio, SubcategoriaServicio
from .serializers import CategoriaServicioSerializer, SubcategoriaServicioSerializer

class CategoriaServicioViewSet(viewsets.ModelViewSet):
    queryset = CategoriaServicio.objects.all()
    serializer_class = CategoriaServicioSerializer

class SubcategoriaServicioViewSet(viewsets.ModelViewSet):
    queryset = SubcategoriaServicio.objects.all()
    serializer_class = SubcategoriaServicioSerializer
