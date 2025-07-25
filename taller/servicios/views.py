from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import CategoriaServicio, SubcategoriaServicio, Servicio
from .serializers import CategoriaServicioSerializer, SubcategoriaServicioSerializer
from rest_framework import serializers
from taller.models import Empresa

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'subcategoria']

@method_decorator(login_required, name='dispatch')
class ServicioViewSet(viewsets.ModelViewSet):
    serializer_class = ServicioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar por empresa del usuario autenticado
        if self.request.user.is_authenticated:
            # Obtener empresa del usuario desde el perfil
            try:
                empresa = self.request.user.perfilusuario.empresa
            except:
                # Si no tiene empresa, buscar o crear una empresa por defecto
                empresa, created = Empresa.objects.get_or_create(
                    nombre=f"Empresa {self.request.user.username}",
                    defaults={'rut': f"00000000-{self.request.user.pk}"}
                )
            
            # Los servicios son globales por categoría, pero requieren autenticación
            return Servicio.objects.all()
        return Servicio.objects.none()

@method_decorator(login_required, name='dispatch')
class CategoriaServicioViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaServicioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Las categorías de servicio son globales pero requieren autenticación
        if self.request.user.is_authenticated:
            return CategoriaServicio.objects.all()
        return CategoriaServicio.objects.none()
