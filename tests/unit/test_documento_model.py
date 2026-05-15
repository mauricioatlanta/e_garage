"""
Tests unitarios para el modelo Documento
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.tecnicos import Tecnico
from taller.models.vehiculos import Vehiculo


class DocumentoModelTest(TestCase):
    """Tests para el modelo Documento"""

    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear empresa de prueba
        self.empresa_cl = Empresa.objects.create(nombre="Taller Chile", pais="CL", rut="12345678-9")

        self.empresa_us = Empresa.objects.create(
            nombre="Auto Center USA", pais="US", rut="123456789"
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre="Juan Pérez", empresa=self.empresa_cl, email="juan@test.com"
        )

        # Crear vehículo
        self.vehiculo = Vehiculo.objects.create(
            marca="Toyota",
            modelo="Corolla",
            año=2020,
            cliente=self.cliente,
            empresa=self.empresa_cl,
        )

        # Crear técnico
        self.tecnico = Tecnico.objects.create(nombre="Carlos Mecánico", empresa=self.empresa_cl)

    def test_crear_documento_basico(self):
        """Test: Crear documento básico"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
        )

        self.assertEqual(doc.empresa, self.empresa_cl)
        self.assertEqual(doc.tipo, "OT")
        self.assertEqual(doc.cliente, self.cliente)
        self.assertEqual(doc.vehiculo, self.vehiculo)
        self.assertEqual(doc.tecnico_responsable, self.tecnico)
        self.assertEqual(doc.country, "CL")
        self.assertEqual(doc.moneda, "CLP")
        self.assertTrue(doc.numero)  # Debe generar número automáticamente

    def test_generar_numero_documento(self):
        """Test: Generación automática de número de documento"""
        # Primer documento
        doc1 = Documento.objects.create(empresa=self.empresa_cl, tipo="OT", cliente=self.cliente)
        self.assertEqual(doc1.numero, "1")

        # Segundo documento
        doc2 = Documento.objects.create(empresa=self.empresa_cl, tipo="OT", cliente=self.cliente)
        self.assertEqual(doc2.numero, "2")

        # Documento de diferente tipo
        doc3 = Documento.objects.create(empresa=self.empresa_cl, tipo="PRES", cliente=self.cliente)
        self.assertEqual(doc3.numero, "1")  # Secuencia independiente por tipo

    def test_numero_documento_property(self):
        """Test: Property numero_documento con prefijos"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl, tipo="OT", cliente=self.cliente, numero="5"
        )

        # Para Chile
        self.assertEqual(doc.numero_documento, "OT005")

        # Para USA
        doc_us = Documento.objects.create(
            empresa=self.empresa_us, tipo="OT", cliente=self.cliente, numero="3"
        )
        self.assertEqual(doc_us.numero_documento, "WO003")

    def test_recompute_totals_chile(self):
        """Test: Recálculo de totales para Chile (IVA 19% solo en repuestos)"""
        doc = Documento.objects.create(empresa=self.empresa_cl, tipo="OT", cliente=self.cliente)

        # Simular líneas de repuesto (IVA aplicable)
        # Mock de las líneas para el test
        class MockLineaRepuesto:
            def __init__(self, cantidad, precio, descuento=0):
                self.cantidad = cantidad
                self.precio_unitario = precio
                self.descuento = descuento

        # Mock del queryset
        doc.lineas_repuesto = [MockLineaRepuesto(2, Decimal("100.00"), 10)]  # 2 * 100 * 0.9 = 180
        doc.lineas_servicio = [MockLineaRepuesto(1, Decimal("50.00"))]  # 1 * 50 = 50
        doc.lineas_otro_servicio = []

        doc.recompute_totals()

        # Verificar cálculos
        self.assertEqual(doc.neto_repuestos, Decimal("180.00"))
        self.assertEqual(doc.neto_servicios, Decimal("50.00"))
        self.assertEqual(doc.neto_otros_servicios, Decimal("0.00"))
        self.assertEqual(doc.tax_rate_applied, Decimal("19.00"))
        # IVA solo sobre repuestos: 180 * 0.19 = 34.2
        self.assertEqual(doc.tax_amount, Decimal("34.20"))
        # Total: 180 + 50 + 0 + 34.2 = 264.2
        self.assertEqual(doc.total, Decimal("264.20"))

    def test_recompute_totals_usa_con_apply_vat(self):
        """Test: Recálculo de totales para USA con apply_vat=True"""
        doc = Documento.objects.create(
            empresa=self.empresa_us, tipo="OT", cliente=self.cliente, apply_vat=True
        )

        # Mock de las líneas
        class MockLinea:
            def __init__(self, cantidad, precio, descuento=0):
                self.cantidad = cantidad
                self.precio_unitario = precio
                self.descuento = descuento

        doc.lineas_repuesto = [MockLinea(1, Decimal("100.00"))]  # 100
        doc.lineas_servicio = [MockLinea(1, Decimal("50.00"))]  # 50
        doc.lineas_otro_servicio = []

        doc.recompute_totals()

        # Para USA con apply_vat=True, impuesto sobre repuestos + servicios
        self.assertEqual(doc.neto_repuestos, Decimal("100.00"))
        self.assertEqual(doc.neto_servicios, Decimal("50.00"))
        self.assertEqual(doc.tax_rate_applied, Decimal("0.00"))  # Por defecto 0% en USA
        self.assertEqual(doc.tax_amount, Decimal("0.00"))
        self.assertEqual(doc.total, Decimal("150.00"))

    def test_recompute_totals_usa_sin_apply_vat(self):
        """Test: Recálculo de totales para USA con apply_vat=False"""
        doc = Documento.objects.create(
            empresa=self.empresa_us, tipo="OT", cliente=self.cliente, apply_vat=False
        )

        # Mock de las líneas
        class MockLinea:
            def __init__(self, cantidad, precio, descuento=0):
                self.cantidad = cantidad
                self.precio_unitario = precio
                self.descuento = descuento

        doc.lineas_repuesto = [MockLinea(1, Decimal("100.00"))]
        doc.lineas_servicio = [MockLinea(1, Decimal("50.00"))]
        doc.lineas_otro_servicio = []

        doc.recompute_totals()

        # Para USA con apply_vat=False, sin impuesto
        self.assertEqual(doc.neto_repuestos, Decimal("100.00"))
        self.assertEqual(doc.neto_servicios, Decimal("50.00"))
        self.assertEqual(doc.tax_amount, Decimal("0.00"))
        self.assertEqual(doc.total, Decimal("150.00"))

    def test_validacion_tecnico_empresa(self):
        """Test: Validación de que técnico pertenece a la empresa"""
        # Crear técnico de otra empresa
        tecnico_otra_empresa = Tecnico.objects.create(
            nombre="Técnico Otra Empresa", empresa=self.empresa_us
        )

        doc = Documento(
            empresa=self.empresa_cl,
            tipo="OT",
            cliente=self.cliente,
            tecnico_responsable=tecnico_otra_empresa,
        )

        with self.assertRaises(ValidationError):
            doc.clean()

    def test_validacion_vehiculo_cliente(self):
        """Test: Validación de que vehículo pertenece al cliente"""
        # Crear otro cliente
        otro_cliente = Cliente.objects.create(
            nombre="Otro Cliente", empresa=self.empresa_cl, email="otro@test.com"
        )

        doc = Documento(
            empresa=self.empresa_cl,
            tipo="OT",
            cliente=otro_cliente,
            vehiculo=self.vehiculo,  # Vehículo de otro cliente
        )

        with self.assertRaises(ValidationError):
            doc.clean()

    def test_validacion_millas_solo_usa(self):
        """Test: Validación de que millas solo se puede usar en USA"""
        doc = Documento(
            empresa=self.empresa_cl,  # Empresa de Chile
            tipo="OT",
            cliente=self.cliente,
            millas=1000,  # Millas en documento de Chile
        )

        with self.assertRaises(ValidationError):
            doc.clean()

    def test_recalcular_totales_bulk(self):
        """Test: Recálculo de totales en lote"""
        # Crear múltiples documentos
        docs = []
        for i in range(3):
            doc = Documento.objects.create(empresa=self.empresa_cl, tipo="OT", cliente=self.cliente)
            docs.append(doc)

        # Recalcular en lote
        documento_ids = [doc.id for doc in docs]
        resultado = Documento.recalcular_totales_bulk(documento_ids)

        self.assertEqual(resultado, 3)

    def test_propiedades_compatibilidad(self):
        """Test: Propiedades de compatibilidad con código antiguo"""
        doc = Documento.objects.create(empresa=self.empresa_cl, tipo="OT", cliente=self.cliente)

        # Verificar propiedades de compatibilidad
        self.assertEqual(doc.total_repuestos(), Decimal("0.00"))
        self.assertEqual(doc.total_servicios(), Decimal("0.00"))
        self.assertEqual(doc.total_otros_servicios(), Decimal("0.00"))
        self.assertEqual(doc.iva(), Decimal("0.00"))
        self.assertEqual(doc.total_general(), Decimal("0.00"))
        self.assertFalse(doc.incluir_iva)
