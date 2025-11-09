from django.test import TestCase


class ModelVehiculosTest(TestCase):
    """Tests para modelos de vehículos"""

    def test_vehiculo_str_and_basic_fields(self):
        """Test __str__ y campos básicos de vehículo"""
        from django.contrib.auth.models import User

        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo

        # Crear empresa y cliente
        user = User.objects.create_user(
            username="testuser_vehiculo", password="testpass"
        )
        emp = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=user)
        cli = Cliente.objects.create(empresa=emp, nombre="Juan", apellido="Pérez")

        # Crear vehículo
        v = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="ABCZ12",
            marca_texto="Toyota",
            modelo_texto="Yaris",
            anio=2018,
        )

        # Verificar campos básicos
        assert str(v)  # __str__ debe retornar algo
        assert v.empresa == emp
        assert v.cliente == cli
        assert v.patente == "ABCZ12"
        assert v.marca_texto == "Toyota"
        assert v.modelo_texto == "Yaris"
        assert v.anio == 2018

    def test_vehiculo_validation(self):
        """Test validación de vehículo"""
        from django.contrib.auth.models import User

        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo

        user = User.objects.create_user(
            username="testuser_vehiculo_val", password="testpass"
        )
        emp = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=user)
        cli = Cliente.objects.create(empresa=emp, nombre="Juan", apellido="Pérez")

        # Crear vehículo válido
        v = Vehiculo(
            empresa=emp,
            cliente=cli,
            patente="XYZ123",
            marca_texto="Honda",
            modelo_texto="Civic",
            anio=2020,
        )
        v.full_clean()  # No debe lanzar excepción

    def test_vehiculo_with_vin(self):
        """Test vehículo con VIN"""
        from django.contrib.auth.models import User

        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo

        user = User.objects.create_user(
            username="testuser_vehiculo_vin", password="testpass"
        )
        emp = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=user)
        cli = Cliente.objects.create(empresa=emp, nombre="Juan", apellido="Pérez")

        v = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="DEF456",
            marca_texto="Ford",
            modelo_texto="Focus",
            anio=2019,
            vin="1HGBH41JXMN109186",
        )

        assert v.vin == "1HGBH41JXMN109186"

    def test_vehiculo_with_millas(self):
        """Test vehículo con millas"""
        from django.contrib.auth.models import User

        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo

        user = User.objects.create_user(
            username="testuser_vehiculo_millas", password="testpass"
        )
        emp = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=user)
        cli = Cliente.objects.create(empresa=emp, nombre="Juan", apellido="Pérez")

        v = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="GHI789",
            marca_texto="Chevrolet",
            modelo_texto="Cruze",
            anio=2021,
            millas=50000,
        )

        assert v.millas == 50000

    def test_vehiculo_empresa_relationship(self):
        """Test relación empresa-vehículo"""
        from django.contrib.auth.models import User

        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo

        user = User.objects.create_user(
            username="testuser_vehiculo_rel", password="testpass"
        )
        emp = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=user)
        cli = Cliente.objects.create(empresa=emp, nombre="Juan", apellido="Pérez")

        v = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="JKL012",
            marca_texto="Nissan",
            modelo_texto="Sentra",
            anio=2022,
        )

        # Verificar que el vehículo pertenece a la empresa
        assert v.empresa == emp
        assert v in emp.vehiculo_set.all()
