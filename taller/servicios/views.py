from rest_framework import viewsets
from .models import CategoriaServicio, SubcategoriaServicio, Servicio
from .serializers import CategoriaServicioSerializer, SubcategoriaServicioSerializer
from rest_framework import serializers

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'subcategoria']

class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer

class CategoriaServicioViewSet(viewsets.ModelViewSet):
    queryset = CategoriaServicio.objects.all()
    serializer_class = CategoriaServicioSerializer
