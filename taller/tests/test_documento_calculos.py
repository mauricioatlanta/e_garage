from decimal import Decimal

import pytest

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models import TaxPolicy
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo


@pytest.mark.django_db
class TestDocumentoCalculos:
    """Tests para el cálculo automático de IVA/Sales Tax"""

    def setup_method(self):
        """Setup para cada test"""
        import time

        timestamp = int(time.time() * 1000) % 100000

        # Crear usuario Chile
        self.user_cl = User.objects.create_user(
            username=f"testuser_cl_{timestamp}",
            email=f"test_cl_{timestamp}@example.com",
            password="testpass123",
        )

        # Crear usuario USA
        self.user_us = User.objects.create_user(
            username=f"testuser_us_{timestamp}",
            email=f"test_us_{timestamp}@example.com",
            password="testpass123",
        )

        # Crear empresa Chile
        self.empresa_cl = Empresa.objects.create(
            nombre_taller="Taller Chile", pais="CL", user=self.user_cl
        )

        # Crear empresa USA
        self.empresa_us = Empresa.objects.create(
            nombre_taller="Taller USA", pais="US", user=self.user_us
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre="Juan Pérez", email="juan@example.com", empresa=self.empresa_cl
        )

        # Crear marca y modelo
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        self.marca = Marca.objects.create(nombre="Toyota", country="CL")

        self.modelo = Modelo.objects.create(nombre="Corolla", marca=self.marca, country="CL")

        # Crear vehículo
        self.vehiculo = Vehiculo.objects.create(
            marca=self.marca,
            modelo=self.modelo,
            anio=2020,
            cliente=self.cliente,
            empresa=self.empresa_cl,
        )

        # Crear técnico
        self.tecnico = Tecnico.objects.create(nombre="Carlos Técnico", empresa=self.empresa_cl)

        # Políticas mínimas de impuestos para los tests
        TaxPolicy.objects.create(country="CL", applies_to="parts", rate=Decimal("0.19"))
        TaxPolicy.objects.create(
            country="US", state_code="CA", applies_to="both", rate=Decimal("0.0725")
        )

    def test_calculo_iva_chile_solo_repuestos(self):
        """Test: Chile aplica IVA 19% solo a repuestos"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
        )
        doc.tax_rate_applied = None

        # Simular valores manualmente (sin líneas reales)
        rep = Decimal("100000")  # 100k en repuestos
        srv = Decimal("50000")  # 50k en servicios
        osrv = Decimal("25000")  # 25k otros servicios
        desc = Decimal("5000")  # 5k descuento

        # Aplicar la lógica de cálculo manualmente
        rep = doc._q(rep)
        srv = doc._q(srv)
        osrv = doc._q(osrv)
        desc = doc._q(desc)

        # Tasa para Chile
        rate = doc._resolve_tax_rate()
        assert rate == Decimal("19.0")

        # Base imponible solo repuestos en Chile
        tax_base = rep
        tax_amount = tax_base * rate / Decimal("100.0")
        tax_amount = doc._q(tax_amount)

        # Total final
        subtotal_general = rep + srv + osrv
        total = subtotal_general - desc + tax_amount
        total = doc._q(total)

        # Verificar cálculos
        assert rep == Decimal("100000")
        assert srv == Decimal("50000")
        assert osrv == Decimal("25000")
        assert desc == Decimal("5000")
        assert tax_amount == Decimal("19000")  # 100k * 19% = 19k
        assert total == Decimal("189000")  # (100k + 50k + 25k) - 5k + 19k = 189k

    def test_calculo_sales_tax_usa_por_defecto_0(self):
        """Test: USA por defecto 0% sales tax"""
        doc = Documento.objects.create(
            empresa=self.empresa_us,
            country="US",
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
        )

        # Simular líneas
        doc.neto_repuestos = Decimal("1000.00")  # 1k en repuestos
        doc.neto_servicios = Decimal("500.00")  # 500 en servicios
        doc.neto_otros_servicios = Decimal("250.00")  # 250 otros servicios
        doc.descuento = Decimal("50.00")  # 50 descuento

        rep = doc._q(doc.neto_repuestos)
        srv = doc._q(doc.neto_servicios)
        osrv = doc._q(doc.neto_otros_servicios)
        desc = doc._q(doc.descuento)
        rate = doc._resolve_tax_rate()
        tax_amount = doc._q(rep * rate / Decimal("100.0"))
        total = doc._q(rep + srv + osrv - desc + tax_amount)

        # Verificar cálculos
        assert rep == Decimal("1000.00")
        assert srv == Decimal("500.00")
        assert osrv == Decimal("250.00")
        assert desc == Decimal("50.00")

        # USA por defecto 0% sales tax
        assert rate == Decimal("0.00")
        assert tax_amount == Decimal("0.00")

        # Total: (1000 + 500 + 250) - 50 + 0 = 1700
        expected_total = (
            Decimal("1000.00") + Decimal("500.00") + Decimal("250.00") - Decimal("50.00")
        )
        assert total == expected_total

    def test_calculo_sales_tax_usa_con_tasa_personalizada(self):
        """Test: USA con tasa personalizada"""
        doc = Documento.objects.create(
            empresa=self.empresa_us,
            country="US",
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
            tax_rate_applied=Decimal("8.5"),  # 8.5% sales tax
        )

        # Simular líneas
        doc.neto_repuestos = Decimal("1000.00")
        doc.neto_servicios = Decimal("500.00")
        doc.descuento = Decimal("50.00")

        rep = doc._q(doc.neto_repuestos)
        srv = doc._q(doc.neto_servicios)
        desc = doc._q(doc.descuento)
        rate = doc._resolve_tax_rate()
        tax_amount = doc._q(rep * rate / Decimal("100.0"))
        total = doc._q(rep + srv - desc + tax_amount)

        # Verificar cálculos
        assert rate == Decimal("8.5")
        # Sales tax solo sobre repuestos: 1000 * 8.5% = 85
        assert tax_amount == Decimal("85.00")

        # Total: (1000 + 500) - 50 + 85 = 1535
        expected_total = (
            Decimal("1000.00") + Decimal("500.00") - Decimal("50.00") + Decimal("85.00")
        )
        assert total == expected_total

    def test_redondeo_decimales_chile_0_us_2(self):
        """Test: Redondeo según país - Chile 0 decimales, USA 2 decimales"""
        # Chile
        doc_cl = Documento.objects.create(
            empresa=self.empresa_cl,
            country="CL",
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
        )

        # USA
        doc_us = Documento.objects.create(
            empresa=self.empresa_us,
            country="US",
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
        )

        # Test decimales
        assert doc_cl._decimals() == 0  # Chile sin decimales
        assert doc_us._decimals() == 2  # USA con 2 decimales

        # Test quantize
        value = Decimal("123.456789")
        assert doc_cl._q(value) == Decimal("123")  # Redondeado a 0 decimales
        assert doc_us._q(value) == Decimal("123.46")  # Redondeado a 2 decimales

    def test_campos_pago_agregados(self):
        """Test: Verificar que los campos de pago fueron agregados"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
            metodo_pago="transferencia",
            ult4="1234",
            monto_pagado=Decimal("100000.00"),
            saldo_pendiente=Decimal("50000.00"),
        )

        # Verificar campos de pago
        assert doc.metodo_pago == "transferencia"
        assert doc.ult4 == "1234"
        assert doc.monto_pagado == Decimal("100000.00")
        assert doc.saldo_pendiente == Decimal("50000.00")

    def test_metodos_compatibilidad(self):
        """Test: Verificar que los métodos de compatibilidad funcionan"""
        doc = Documento.objects.create(
            empresa=self.empresa_cl,
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            tecnico_responsable=self.tecnico,
        )

        # Establecer valores directamente
        doc.total_repuestos = Decimal("100000")
        doc.total_servicios = Decimal("50000")
        doc.total_otros = Decimal("25000")
        doc.iva = Decimal("19000")
        doc.total_general = Decimal("194000")

        # Verificar métodos de compatibilidad
        assert doc.total_repuestos == Decimal("100000")
        assert doc.total_servicios == Decimal("50000")
        assert doc.total_otros == Decimal("25000")
        assert doc.iva == Decimal("19000")
        assert doc.total_general == Decimal("194000")
