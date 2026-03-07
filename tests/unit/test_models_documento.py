"""
Tests para modelos de documento - cobertura rápida de validaciones y métodos
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaServicio
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo


class DocumentoModelTest(TestCase):
    """Tests básicos para el modelo Documento"""

    def setUp(self):
        """Setup básico para tests"""
        # Crear usuario para la empresa
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="testuser", password="testpass")

        # Crear empresa
        self.empresa = Empresa.objects.create(
            user=self.user, nombre_taller="Test Garage", pais="CL"
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(empresa=self.empresa, nombre="Cliente Test")

        # Crear vehículo
        self.vehiculo = Vehiculo.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            patente="ABC123",
            marca_texto="Toyota",
            modelo_texto="Corolla",
            anio=2020,
        )

        # Crear técnico
        self.tecnico = Tecnico.objects.create(empresa=self.empresa, nombre="Técnico Test")

    def test_documento_creation(self):
        """Test creación básica de documento"""
        doc = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tipo="OT",
            estado="EMITIDO",
        )

        self.assertEqual(doc.empresa, self.empresa)
        self.assertEqual(doc.cliente, self.cliente)
        self.assertEqual(doc.vehiculo, self.vehiculo)
        self.assertEqual(doc.tipo, "OT")
        self.assertEqual(doc.estado, "EMITIDO")
        self.assertEqual(doc.country, "CL")  # Default
        self.assertEqual(doc.moneda, "CLP")  # Default

    def test_documento_clean_validation_tecnico_empresa(self):
        """Test validación de técnico perteneciente a la empresa"""
        # Crear otro usuario para otra empresa
        from django.contrib.auth.models import User

        otro_user = User.objects.create_user(username="otrouser", password="testpass")

        # Crear otra empresa
        otra_empresa = Empresa.objects.create(
            user=otro_user, nombre_taller="Otra Empresa", pais="CL"
        )

        # Crear técnico de otra empresa
        tecnico_otra_empresa = Tecnico.objects.create(
            empresa=otra_empresa, nombre="Técnico Otra Empresa"
        )

        # Intentar crear documento con técnico de otra empresa
        doc = Documento(
            empresa=self.empresa,
            cliente=self.cliente,
            tecnico_responsable=tecnico_otra_empresa,
            tipo="OT",
        )

        with self.assertRaises(ValidationError) as cm:
            doc.full_clean()

        self.assertIn(
            "El técnico responsable debe pertenecer a la misma empresa",
            str(cm.exception),
        )

    def test_documento_clean_validation_millas_usa(self):
        """Test validación de millas solo para USA"""
        doc = Documento(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="OT",
            country="CL",  # Chile
            millas=50000,  # Millas en Chile (debería fallar)
        )

        with self.assertRaises(ValidationError) as cm:
            doc.full_clean()

        self.assertIn("El campo millas solo puede usarse en documentos de USA", str(cm.exception))

    def test_documento_clean_validation_millas_usa_ok(self):
        """Test que millas funciona correctamente en USA"""
        doc = Documento(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="OT",
            country="US",
            millas=50000,
        )

        # No debería lanzar excepción
        doc.full_clean()

    def test_numero_documento_property(self):
        """Test propiedad numero_documento"""
        doc = Documento.objects.create(
            empresa=self.empresa, cliente=self.cliente, tipo="OT", numero="123"
        )

        # Para Chile, OT debería tener prefijo "OT"
        self.assertEqual(doc.numero_documento, "OT123")

    def test_numero_documento_property_usa(self):
        """Test propiedad numero_documento para USA"""
        doc = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="OT",
            numero="123",
            country="US",
        )

        # Para USA, OT debería tener prefijo "WO"
        self.assertEqual(doc.numero_documento, "WO123")

    def test_numero_documento_property_sin_numero(self):
        """Test propiedad numero_documento sin número"""
        # Crear documento sin especificar número
        doc = Documento(empresa=self.empresa, cliente=self.cliente, tipo="OT")
        # No llamar save() para evitar generación automática

        # Verificar que retorna None cuando no hay número
        self.assertIsNone(doc.numero_documento)

    def test_tipo_documento_property(self):
        """Test propiedad tipo_documento"""
        doc = Documento.objects.create(empresa=self.empresa, cliente=self.cliente, tipo="FAC")

        self.assertEqual(doc.tipo_documento, "FAC")

    def test_incluir_iva_property(self):
        """Test propiedad incluir_iva"""
        doc = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="FAC",
            tax_rate_applied=Decimal("19.00"),
        )

        self.assertTrue(doc.incluir_iva)

        doc.tax_rate_applied = Decimal("0.00")
        self.assertFalse(doc.incluir_iva)

    def test_total_repuestos_empty(self):
        """Test método total_repuestos sin líneas"""
        doc = Documento.objects.create(empresa=self.empresa, cliente=self.cliente, tipo="OT")

        # Sin líneas de repuesto, debería retornar 0
        self.assertEqual(doc.total_repuestos(), 0)

    def test_total_servicios_empty(self):
        """Test método total_servicios sin líneas"""
        doc = Documento.objects.create(empresa=self.empresa, cliente=self.cliente, tipo="OT")

        # Sin líneas de servicio, debería retornar 0
        self.assertEqual(doc.total_servicios(), 0)

    def test_total_otros_servicios_empty(self):
        """Test método total_otros_servicios sin líneas"""
        doc = Documento.objects.create(empresa=self.empresa, cliente=self.cliente, tipo="OT")

        # Sin líneas de otros servicios, debería retornar 0
        self.assertEqual(doc.total_otros_servicios(), 0)

    def test_iva_calculation(self):
        """Test cálculo de IVA"""
        doc = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="FAC",
            tax_rate_applied=Decimal("19.00"),
            descuento=Decimal("0.00"),
        )

        # Sin líneas, IVA debería ser 0
        self.assertEqual(doc.iva(), 0)

    def test_total_general(self):
        """Test método total_general"""
        doc = Documento.objects.create(empresa=self.empresa, cliente=self.cliente, tipo="OT")

        # Sin líneas, total debería ser 0
        self.assertEqual(doc.total_general(), 0)

    def test_recalcular_totales(self):
        """Test método recalcular_totales"""
        doc = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            tipo="FAC",
            country="CL",
            apply_vat=True,
        )

        # Recalcular totales (sin líneas)
        doc.recalcular_totales()

        # Verificar que se actualizaron los campos
        self.assertEqual(doc.neto_repuestos, 0)
        self.assertEqual(doc.neto_servicios, 0)
        self.assertEqual(doc.tax_amount, 0)
        self.assertEqual(doc.total, 0)

    def test_properties_retrocompatibles(self):
        """Test propiedades retrocompatibles"""
        doc = Documento.objects.create(empresa=self.empresa, cliente=self.cliente, tipo="OT")

        # Estas propiedades deberían retornar los related managers
        self.assertEqual(doc.repuestos, doc.lineas_repuesto)
        self.assertEqual(doc.servicios, doc.lineas_servicio)
        self.assertEqual(doc.otros_servicios, doc.lineas_otro_servicio)

    def test_str_representation(self):
        """Test representación string del modelo"""
        doc = Documento.objects.create(
            empresa=self.empresa, cliente=self.cliente, tipo="OT", numero="123"
        )

        # Verificar que __str__ no lanza excepción
        str_repr = str(doc)
        self.assertIsInstance(str_repr, str)

    def test_signals_documento_total_updated_on_linea_servicio(self):
        """
        Smoke test: al crear una LineaServicio, el signal debe recalcular
        Documento.total (signals_documento registrados en apps.ready).
        Si este test falla, revisar que taller.apps.TallerConfig.ready()
        importe taller.models.signals_documento.
        """
        doc = Documento.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tipo="OT",
            estado="EMITIDO",
        )
        doc.refresh_from_db()
        before = doc.total

        LineaServicio.objects.create(
            documento=doc,
            nombre="TEST SIGNALS",
            cantidad=1,
            precio_unitario=Decimal("100"),
            descuento=Decimal("0"),
        )

        doc.refresh_from_db()
        self.assertGreater(
            doc.total,
            before,
            "Documento.total debe aumentar al crear LineaServicio (signals_documento).",
        )
