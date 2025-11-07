import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError


class ModelAdicionalesTest(TestCase):
    """Tests para modelos adicionales"""

    def test_marca_str_method(self):
        """Test método __str__ de Marca"""
        from taller.models.marca import Marca

        marca = Marca.objects.create(
            nombre="Toyota",
            country="CL"
        )
        
        str_repr = str(marca)
        assert str_repr
        assert "Toyota" in str_repr

    def test_modelo_str_method(self):
        """Test método __str__ de Modelo"""
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        marca = Marca.objects.create(
            nombre="Toyota",
            country="CL"
        )
        modelo = Modelo.objects.create(
            nombre="Yaris",
            country="CL",
            marca=marca
        )
        
        str_repr = str(modelo)
        assert str_repr
        assert "Yaris" in str_repr

    def test_caja_vehiculo_str_method(self):
        """Test método __str__ de CajaVehiculo"""
        from taller.models.extras_vehiculo import CajaVehiculo

        caja = CajaVehiculo.objects.create(
            nombre="Manual 5 velocidades"
        )
        
        str_repr = str(caja)
        assert str_repr
        assert "Manual" in str_repr

    def test_motor_vehiculo_str_method(self):
        """Test método __str__ de MotorVehiculo"""
        from taller.models.extras_vehiculo import MotorVehiculo

        motor = MotorVehiculo.objects.create(
            nombre="1.6L 4 cilindros"
        )
        
        str_repr = str(motor)
        assert str_repr
        assert "1.6L" in str_repr

    def test_catalogo_modelo_auto_str_method(self):
        """Test método __str__ de CatalogoModeloAuto"""
        from taller.models.catalogo import CatalogoModeloAuto

        catalogo = CatalogoModeloAuto.objects.create(
            marca="Toyota",
            modelo="Yaris",
            activo=True
        )
        
        str_repr = str(catalogo)
        assert str_repr
        assert "Toyota" in str_repr
        assert "Yaris" in str_repr

    def test_marca_validation(self):
        """Test validación de Marca"""
        from taller.models.marca import Marca

        marca = Marca(
            nombre="Honda",
            country="CL"
        )
        marca.full_clean()  # No debe lanzar excepción

    def test_modelo_validation(self):
        """Test validación de Modelo"""
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        marca = Marca.objects.create(
            nombre="Honda",
            country="CL"
        )
        modelo = Modelo(
            nombre="Civic",
            country="CL",
            marca=marca
        )
        modelo.full_clean()  # No debe lanzar excepción

    def test_caja_vehiculo_validation(self):
        """Test validación de CajaVehiculo"""
        from taller.models.extras_vehiculo import CajaVehiculo

        caja = CajaVehiculo(
            nombre="Automática 4 velocidades"
        )
        caja.full_clean()  # No debe lanzar excepción

    def test_motor_vehiculo_validation(self):
        """Test validación de MotorVehiculo"""
        from taller.models.extras_vehiculo import MotorVehiculo

        motor = MotorVehiculo(
            nombre="2.0L Turbo"
        )
        motor.full_clean()  # No debe lanzar excepción

    def test_catalogo_modelo_auto_validation(self):
        """Test validación de CatalogoModeloAuto"""
        from taller.models.catalogo import CatalogoModeloAuto

        catalogo = CatalogoModeloAuto(
            marca="Ford",
            modelo="Focus",
            activo=True
        )
        catalogo.full_clean()  # No debe lanzar excepción

    def test_marca_unique_constraint(self):
        """Test constraint único de Marca"""
        from taller.models.marca import Marca

        # Crear primera marca
        Marca.objects.create(
            nombre="Nissan",
            country="CL"
        )
        
        # Intentar crear marca duplicada
        marca_duplicada = Marca(
            nombre="Nissan",
            country="CL"
        )
        
        # Debe lanzar excepción por constraint único
        with pytest.raises(ValidationError):
            marca_duplicada.full_clean()

    def test_modelo_relationship_with_marca(self):
        """Test relación Modelo-Marca"""
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        marca = Marca.objects.create(
            nombre="Mazda",
            country="CL"
        )
        modelo = Modelo.objects.create(
            nombre="CX-5",
            country="CL",
            marca=marca
        )
        
        # Verificar relación
        assert modelo.marca == marca
        assert modelo in marca.modelo_set.all()
