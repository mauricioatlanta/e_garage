#!/usr/bin/env python3
"""
Tests backend para verificar cálculos de documentos
Garantiza que los totales, IVA, subtotales y coherencia país-empresa
sean correctos y reflejen exactamente lo que el frontend calcula.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from taller.models import (
    Cliente,
    Documento,
    Empresa,
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
    Marca,
    Tecnico,
    Vehiculo,
)

User = get_user_model()


class TestDocumentoBackend(TestCase):
    """Tests para verificar cálculos de documentos en el backend"""

    def setUp(self):
        """Configuración inicial para todos los tests"""
        # Usuarios
        self.user_cl = User.objects.create_user(username="tester_cl", password="testpass123")

        self.user_us = User.objects.create_user(username="tester_us", password="testpass123")

        # Empresa CL (Chile)
        self.empresa_cl = Empresa.objects.create(
            user=self.user_cl, nombre_taller="DemoCL", pais="CL", moneda="CLP"
        )

        # Empresa US (Estados Unidos)
        self.empresa_us = Empresa.objects.create(
            user=self.user_us, nombre_taller="DemoUS", pais="US", moneda="USD"
        )

        self.tecnico_cl = Tecnico.objects.create(empresa=self.empresa_cl, nombre="Juan Tech CL")

        self.tecnico_us = Tecnico.objects.create(empresa=self.empresa_us, nombre="John Tech US")

        # Marcas
        self.marca_toyota = Marca.objects.create(nombre="Toyota", country="CL")

        self.marca_ford = Marca.objects.create(nombre="Ford", country="US")

        # Cliente y vehículo para Chile
        self.cliente_cl = Cliente.objects.create(empresa=self.empresa_cl, nombre="Cliente A")

        self.vehiculo_cl = Vehiculo.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            patente="AA1234",
            marca=self.marca_toyota,
            modelo="Corolla",
        )

        # Cliente y vehículo para Estados Unidos
        self.cliente_us = Cliente.objects.create(empresa=self.empresa_us, nombre="Customer B")

        self.vehiculo_us = Vehiculo.objects.create(
            empresa=self.empresa_us,
            cliente=self.cliente_us,
            patente="BB5678",
            marca=self.marca_ford,
            modelo="Focus",
        )

    def test_totales_chile_con_iva(self):
        """Test: Verificar cálculos de totales en Chile con IVA 19%"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Repuestos (con IVA 19%)
        LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro de aire",
            cantidad=2,
            precio_unitario=Decimal("10000"),
            codigo="FIL001",
        )

        # Servicios (sin IVA)
        LineaServicio.objects.create(
            documento=doc,
            nombre="Cambio de aceite",
            cantidad=1,
            precio_unitario=Decimal("5000"),
        )

        # Otros/externos (sin IVA)
        LineaOtroServicio.objects.create(
            documento=doc, nombre="Balanceo", cantidad=1, precio_cliente=Decimal("3000")
        )

        # Recalcular totales
        doc.recalcular_totales()
        doc.refresh_from_db()

        # Verificar cálculos
        self.assertEqual(doc.total_repuestos, Decimal("20000"))  # 2 * 10000
        self.assertEqual(doc.total_servicios, Decimal("5000"))  # 1 * 5000
        self.assertEqual(doc.total_otros, Decimal("3000"))  # 1 * 3000
        self.assertEqual(doc.iva, Decimal("3800"))  # 19% de 20000
        self.assertEqual(doc.total_general, Decimal("31800"))  # 20000 + 5000 + 3000 + 3800

    def test_totales_usa_sin_iva(self):
        """Test: Verificar cálculos de totales en Estados Unidos sin IVA"""
        doc = Documento.objects.create(
            empresa=self.empresa_us,
            cliente=self.cliente_us,
            vehiculo=self.vehiculo_us,
            tecnico_responsable=self.tecnico_us,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_us,
            updated_by=self.user_us,
        )

        # Repuestos (sin IVA en US)
        LineaRepuesto.objects.create(
            documento=doc,
            nombre="Brake Pad",
            cantidad=1,
            precio_unitario=Decimal("100"),
            codigo="BP001",
        )

        # Servicios (sin IVA en US)
        LineaServicio.objects.create(
            documento=doc, nombre="Labor", cantidad=1, precio_unitario=Decimal("50")
        )

        # Recalcular totales
        doc.recalcular_totales()
        doc.refresh_from_db()

        # Verificar cálculos
        self.assertEqual(doc.total_repuestos, Decimal("100"))  # 1 * 100
        self.assertEqual(doc.total_servicios, Decimal("50"))  # 1 * 50
        self.assertEqual(doc.total_otros, Decimal("0"))  # Sin otros servicios
        self.assertEqual(doc.iva, Decimal("0"))  # 0% en US
        self.assertEqual(doc.total_general, Decimal("150"))  # 100 + 50 + 0 + 0

    def test_subtotales_por_linea(self):
        """Test: Verificar que los subtotales por línea se calculan correctamente"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Línea de repuesto
        linea_repuesto = LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro",
            cantidad=3,
            precio_unitario=Decimal("5000"),
            codigo="FIL002",
        )

        # Línea de servicio
        linea_servicio = LineaServicio.objects.create(
            documento=doc,
            nombre="Revisión",
            cantidad=2,
            precio_unitario=Decimal("3000"),
        )

        # Línea de otro servicio
        linea_otro = LineaOtroServicio.objects.create(
            documento=doc, nombre="Balanceo", cantidad=1, precio_cliente=Decimal("4000")
        )

        # Verificar subtotales individuales
        self.assertEqual(linea_repuesto.subtotal, Decimal("15000"))  # 3 * 5000
        self.assertEqual(linea_servicio.subtotal, Decimal("6000"))  # 2 * 3000
        self.assertEqual(linea_otro.subtotal, Decimal("4000"))  # 1 * 4000

    def test_coherencia_empresa_cliente_vehiculo(self):
        """Test: Verificar que empresa, cliente y vehículo son coherentes"""
        # Crear documento con empresa CL
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Verificar coherencia
        self.assertEqual(doc.empresa, self.empresa_cl)
        self.assertEqual(doc.cliente.empresa, self.empresa_cl)
        self.assertEqual(doc.vehiculo.empresa, self.empresa_cl)
        self.assertEqual(doc.tecnico_responsable.empresa, self.empresa_cl)

    def test_audit_fields(self):
        """Test: Verificar que los campos de auditoría se completan"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Verificar campos de auditoría
        self.assertEqual(doc.created_by, self.user)
        self.assertEqual(doc.updated_by, self.user)
        self.assertIsNotNone(doc.created_at)
        self.assertIsNotNone(doc.updated_at)

    def test_clean_validation(self):
        """Test: Verificar que Documento.clean() valida coherencia"""
        # Crear documento con empresa CL
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # clean() no debe lanzar excepción
        try:
            doc.clean()
        except Exception as e:
            self.fail(f"Documento.clean() lanzó excepción: {e}")

    def test_moneda_por_pais(self):
        """Test: Verificar que la moneda se determina correctamente por país"""
        # Documento Chile
        doc_cl = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Documento Estados Unidos
        doc_us = Documento.objects.create(
            empresa=self.empresa_us,
            cliente=self.cliente_us,
            vehiculo=self.vehiculo_us,
            tecnico_responsable=self.tecnico_us,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Verificar monedas
        self.assertEqual(doc_cl.empresa.moneda, "CLP")
        self.assertEqual(doc_us.empresa.moneda, "USD")

    def test_iva_calculation_edge_cases(self):
        """Test: Verificar casos límite en el cálculo de IVA"""
        # Documento Chile con solo servicios (sin IVA)
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Solo servicios (sin repuestos)
        LineaServicio.objects.create(
            documento=doc,
            nombre="Revisión",
            cantidad=1,
            precio_unitario=Decimal("10000"),
        )

        doc.recalcular_totales()
        doc.refresh_from_db()

        # IVA debe ser 0 porque no hay repuestos
        self.assertEqual(doc.iva, Decimal("0"))
        self.assertEqual(doc.total_general, Decimal("10000"))

    def test_descuentos_en_repuestos(self):
        """Test: Verificar que los descuentos se aplican correctamente"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Repuesto con descuento del 10%
        LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro con descuento",
            cantidad=1,
            precio_unitario=Decimal("10000"),
            descuento=Decimal("10.00"),  # 10%
            codigo="FIL003",
        )

        doc.recalcular_totales()
        doc.refresh_from_db()

        # Subtotal con descuento: 10000 - (10000 * 0.10) = 9000
        # IVA: 19% de 9000 = 1710
        # Total: 9000 + 1710 = 10710
        self.assertEqual(doc.total_repuestos, Decimal("9000"))
        self.assertEqual(doc.iva, Decimal("1710"))
        self.assertEqual(doc.total_general, Decimal("10710"))

    def test_multiple_repuestos_con_iva(self):
        """Test: Verificar IVA con múltiples repuestos"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente_cl,
            vehiculo=self.vehiculo_cl,
            tecnico_responsable=self.tecnico_cl,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Múltiples repuestos
        LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro 1",
            cantidad=2,
            precio_unitario=Decimal("5000"),
            codigo="FIL004",
        )

        LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro 2",
            cantidad=1,
            precio_unitario=Decimal("8000"),
            codigo="FIL005",
        )

        doc.recalcular_totales()
        doc.refresh_from_db()

        # Total repuestos: (2 * 5000) + (1 * 8000) = 18000
        # IVA: 19% de 18000 = 3420
        # Total: 18000 + 3420 = 21420
        self.assertEqual(doc.total_repuestos, Decimal("18000"))
        self.assertEqual(doc.iva, Decimal("3420"))
        self.assertEqual(doc.total_general, Decimal("21420"))


# Tests adicionales para casos específicos
class TestDocumentoEdgeCases(TestCase):
    """Tests para casos límite y edge cases"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.empresa_cl = Empresa.objects.create(
            user=self.user, nombre_taller="TestCL", pais="CL", moneda="CLP"
        )

        # Marca
        self.marca_test = Marca.objects.create(nombre="Test", country="CL")

        self.tecnico = Tecnico.objects.create(empresa=self.empresa_cl, nombre="Test Tech")

        self.cliente = Cliente.objects.create(empresa=self.empresa_cl, nombre="Test Client")

        self.vehiculo = Vehiculo.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente,
            patente="TEST01",
            marca=self.marca_test,
            modelo="Model",
        )

    def test_documento_sin_lineas(self):
        """Test: Documento sin líneas debe tener totales en 0"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        doc.recalcular_totales()
        doc.refresh_from_db()

        self.assertEqual(doc.total_repuestos, Decimal("0"))
        self.assertEqual(doc.total_servicios, Decimal("0"))
        self.assertEqual(doc.total_otros, Decimal("0"))
        self.assertEqual(doc.iva, Decimal("0"))
        self.assertEqual(doc.total_general, Decimal("0"))

    def test_precios_con_decimales(self):
        """Test: Verificar manejo de precios con decimales"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
            fecha_emision=timezone.now(),
            tipo="OT",
            created_by=self.user_cl,
            updated_by=self.user_cl,
        )

        # Precio con decimales
        LineaRepuesto.objects.create(
            documento=doc,
            nombre="Filtro decimal",
            cantidad=1,
            precio_unitario=Decimal("10000.50"),
            codigo="FIL006",
        )

        doc.recalcular_totales()
        doc.refresh_from_db()

        # IVA: 19% de 10000.50 = 1900.095, redondeado a 1900.10
        self.assertEqual(doc.total_repuestos, Decimal("10000.50"))
        self.assertEqual(doc.iva, Decimal("1900.10"))
        self.assertEqual(doc.total_general, Decimal("11900.60"))
