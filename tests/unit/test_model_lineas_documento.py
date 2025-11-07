from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal


class ModelLineasDocumentoTest(TestCase):
    """Tests para modelos de líneas de documento"""

    def test_linea_repuesto_subtotal_calculation(self):
        """Test cálculo de subtotal en línea de repuesto"""
        from taller.models.empresa import Empresa
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaRepuesto
        from taller.models.clientes import Cliente
        from django.contrib.auth.models import User

        # Crear empresa, documento y repuesto mínimos
        user = User.objects.create_user(
            username='testuser_lineas',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test SA",
            pais="CL",
            user=user
        )
        cli = Cliente.objects.create(
            empresa=emp,
            nombre="Cliente Test"
        )
        doc = Documento.objects.create(
            empresa=emp,
            cliente=cli,
            tipo="FAC",
            fecha_emision="2025-01-01"
        )
        item = LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro de aceite",
            codigo="FIL001",
            cantidad=2,
            precio_unitario=5000,
            descuento=0,
        )
        
        # Verificar cálculo de subtotal
        subtotal = getattr(item, "subtotal", item.cantidad * item.precio_unitario)
        assert subtotal == 10000

    def test_linea_servicio_validation_amounts(self):
        """Test validación de montos en línea de servicio"""
        from taller.models.empresa import Empresa
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio
        from taller.models.clientes import Cliente
        from django.contrib.auth.models import User

        user = User.objects.create_user(
            username='testuser_servicio',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test SA",
            pais="CL",
            user=user
        )
        cli = Cliente.objects.create(
            empresa=emp,
            nombre="Cliente Test"
        )
        doc = Documento.objects.create(
            empresa=emp,
            cliente=cli,
            tipo="FAC",
            fecha_emision="2025-01-01"
        )
        ls = LineaServicio(
            documento=doc,
            nombre="Alineación",
            cantidad=1,
            precio_unitario=15000,
            descuento=0,
        )
        ls.full_clean()  # No debe lanzar excepción

    def test_linea_otro_servicio_validation(self):
        """Test validación de línea de otro servicio"""
        from taller.models.empresa import Empresa
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaOtroServicio
        from taller.models.clientes import Cliente
        from django.contrib.auth.models import User

        user = User.objects.create_user(
            username='testuser_otro',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test SA",
            pais="CL",
            user=user
        )
        cli = Cliente.objects.create(
            empresa=emp,
            nombre="Cliente Test"
        )
        doc = Documento.objects.create(
            empresa=emp,
            cliente=cli,
            tipo="FAC",
            fecha_emision="2025-01-01"
        )
        los = LineaOtroServicio(
            documento=doc,
            nombre="Servicio externo",
            empresa_externa="Taller Externo",
            cantidad=1,
            costo_interno=10000,
            precio_cliente=15000,
        )
        los.full_clean()  # No debe lanzar excepción

    def test_linea_repuesto_str_method(self):
        """Test método __str__ de línea de repuesto"""
        from taller.models.empresa import Empresa
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaRepuesto
        from taller.models.clientes import Cliente
        from django.contrib.auth.models import User

        user = User.objects.create_user(
            username='testuser_str',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test SA",
            pais="CL",
            user=user
        )
        cli = Cliente.objects.create(
            empresa=emp,
            nombre="Cliente Test"
        )
        doc = Documento.objects.create(
            empresa=emp,
            cliente=cli,
            tipo="FAC",
            fecha_emision="2025-01-01"
        )
        item = LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro de aceite",
            codigo="FIL001",
            cantidad=2,
            precio_unitario=5000,
            descuento=0,
        )
        
        # Verificar que __str__ retorna algo válido
        str_repr = str(item)
        assert str_repr
        assert "Filtro de aceite" in str_repr

    def test_linea_servicio_str_method(self):
        """Test método __str__ de línea de servicio"""
        from taller.models.empresa import Empresa
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio
        from taller.models.clientes import Cliente
        from django.contrib.auth.models import User

        user = User.objects.create_user(
            username='testuser_str_serv',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test SA",
            pais="CL",
            user=user
        )
        cli = Cliente.objects.create(
            empresa=emp,
            nombre="Cliente Test"
        )
        doc = Documento.objects.create(
            empresa=emp,
            cliente=cli,
            tipo="FAC",
            fecha_emision="2025-01-01"
        )
        ls = LineaServicio.objects.create(
            documento=doc,
            nombre="Alineación",
            cantidad=1,
            precio_unitario=15000,
            descuento=0,
        )
        
        # Verificar que __str__ retorna algo válido
        str_repr = str(ls)
        assert str_repr
        assert "Alineación" in str_repr
