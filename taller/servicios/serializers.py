
from rest_framework import serializers
from .models import CategoriaServicio, SubcategoriaServicio

class SubcategoriaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubcategoriaServicio
        fields = ['id', 'nombre', 'categoria']

class CategoriaServicioSerializer(serializers.ModelSerializer):
    subcategorias = SubcategoriaServicioSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriaServicio
        fields = ['id', 'nombre', 'subcategorias']
