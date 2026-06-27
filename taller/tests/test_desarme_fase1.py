"""
Tests mínimos fase 1 módulo Desarme.
- Vehiculo: CLIENTE exige cliente; DESARME exige cliente null.
- LineaRepuesto: STOCK_BODEGA exige repuesto o part; DESARME exige pieza_desarme y stock.
- InventoryService: STOCK_BODEGA descuenta Repuesto; DESARME descuenta PiezaDesarme; EXTERNO no mueve; repone al anular.
"""

from decimal import Decimal

import pytest

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_DESARME,
    ORIGEN_EXTERNO,
    ORIGEN_STOCK_BODEGA,
)
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.repuesto import Repuesto
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.services.inventory_service import InventoryService


@pytest.mark.django_db
class TestVehiculoDesarme:
    """Vehiculo: CLIENTE exige cliente; DESARME exige cliente null."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="test_vehiculo_desarme",
            email="test_veh@test.com",
            password="testpass",
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Test", pais="CL", user=self.user, plan="paid"
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test", apellido="Uno", email="c1@test.com", empresa=self.empresa
        )

    def test_tipo_cliente_exige_cliente(self):
        v = Vehiculo(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente=None,
            patente="ABC123",
            anio=2020,
        )
        with pytest.raises(ValidationError) as exc:
            v.clean()
        assert "cliente" in str(exc.value).lower() or "asignado" in str(exc.value).lower()

    def test_tipo_desarme_exige_cliente_null(self):
        v = Vehiculo(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_DESARME,
            cliente=self.cliente,
            patente="DES001",
            anio=2019,
        )
        with pytest.raises(ValidationError) as exc:
            v.clean()
        assert "desarme" in str(exc.value).lower() or "cliente" in str(exc.value).lower()

    def test_tipo_cliente_valido_con_cliente(self):
        v = Vehiculo(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente=self.cliente,
            patente="OK001",
            anio=2020,
        )
        v.clean()  # no raise

    def test_tipo_desarme_valido_sin_cliente(self):
        v = Vehiculo(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_DESARME,
            cliente=None,
            patente="OKD01",
            anio=2019,
        )
        v.clean()  # no raise


@pytest.mark.django_db
class TestLineaRepuestoOrigen:
    """LineaRepuesto: STOCK_BODEGA exige repuesto o part; DESARME exige pieza_desarme y stock."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="test_linea_desarme",
            email="test_ln@test.com",
            password="testpass",
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Test", pais="CL", user=self.user, plan="paid"
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente", apellido="Test", email="c@test.com", empresa=self.empresa
        )
        self.vehiculo_cliente = Vehiculo.objects.create(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente=self.cliente,
            patente="PAT01",
            anio=2020,
        )
        self.vehiculo_desarme = VehiculoDesarme.objects.create(
            empresa=self.empresa,
            patente="DES01",
            anio=2018,
        )
        self.documento = Documento.objects.create(
            empresa=self.empresa,
            tipo="OT",
            cliente=self.cliente,
            vehiculo=self.vehiculo_cliente,
        )
        self.repuesto = Repuesto.objects.create(
            empresa=self.empresa,
            nombre="Repuesto Test",
            part_number="R001",
            cantidad_stock=10,
        )
        self.pieza = PiezaDesarme.objects.create(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo_desarme,
            codigo="PZ01",
            nombre="Pieza Desarme",
            cantidad=5,
        )

    def test_stock_bodega_sin_repuesto_ni_part_falla(self):
        linea = LineaRepuesto(
            documento=self.documento,
            origen_repuesto=ORIGEN_STOCK_BODEGA,
            repuesto=None,
            part=None,
            codigo="X",
            nombre="Item",
            cantidad=1,
            precio_unitario=Decimal("100"),
        )
        with pytest.raises(ValidationError):
            linea.clean()

    def test_stock_bodega_con_repuesto_pasa(self):
        linea = LineaRepuesto(
            documento=self.documento,
            origen_repuesto=ORIGEN_STOCK_BODEGA,
            repuesto=self.repuesto,
            codigo="R001",
            nombre=self.repuesto.nombre,
            cantidad=1,
            precio_unitario=Decimal("100"),
        )
        linea.clean()  # no raise

    def test_desarme_sin_pieza_falla(self):
        linea = LineaRepuesto(
            documento=self.documento,
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=None,
            codigo="PZ",
            nombre="Pieza",
            cantidad=1,
            precio_unitario=Decimal("50"),
        )
        with pytest.raises(ValidationError):
            linea.clean()

    def test_desarme_sin_stock_suficiente_falla(self):
        linea = LineaRepuesto(
            documento=self.documento,
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=self.pieza,
            codigo="PZ01",
            nombre=self.pieza.nombre,
            cantidad=10,
            precio_unitario=Decimal("50"),
        )
        # pieza tiene cantidad=5
        with pytest.raises(ValidationError) as exc:
            linea.clean()
        assert "insuficiente" in str(exc.value).lower() or "stock" in str(exc.value).lower()

    def test_desarme_con_stock_pasa(self):
        linea = LineaRepuesto(
            documento=self.documento,
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=self.pieza,
            codigo="PZ01",
            nombre=self.pieza.nombre,
            cantidad=2,
            precio_unitario=Decimal("50"),
        )
        linea.clean()  # no raise


@pytest.mark.django_db
class TestInventoryServiceDesarme:
    """InventoryService: descuenta Repuesto (STOCK_BODEGA), PiezaDesarme (DESARME); EXTERNO no mueve; repone al anular."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="test_inv_desarme",
            email="test_inv@test.com",
            password="testpass",
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Inv", pais="CL", user=self.user, plan="paid"
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente", apellido="Inv", email="ci@test.com", empresa=self.empresa
        )
        self.vehiculo_cliente = Vehiculo.objects.create(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente=self.cliente,
            patente="INV01",
            anio=2020,
        )
        self.vehiculo_desarme = VehiculoDesarme.objects.create(
            empresa=self.empresa,
            patente="INVD",
            anio=2018,
        )
        self.repuesto = Repuesto.objects.create(
            empresa=self.empresa,
            nombre="Repuesto Inv",
            part_number="INV-R",
            cantidad_stock=10,
        )
        self.pieza = PiezaDesarme.objects.create(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo_desarme,
            codigo="INV-P",
            nombre="Pieza Inv",
            cantidad=5,
        )
        self.documento = Documento.objects.create(
            empresa=self.empresa,
            tipo="OT",
            estado="EMITIDO",
            cliente=self.cliente,
            vehiculo=self.vehiculo_cliente,
        )
        self.linea_bodega = LineaRepuesto.objects.create(
            documento=self.documento,
            origen_repuesto=ORIGEN_STOCK_BODEGA,
            repuesto=self.repuesto,
            codigo="INV-R",
            nombre=self.repuesto.nombre,
            cantidad=3,
            precio_unitario=Decimal("100"),
        )
        self.linea_desarme = LineaRepuesto.objects.create(
            documento=self.documento,
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=self.pieza,
            codigo="INV-P",
            nombre=self.pieza.nombre,
            cantidad=2,
            precio_unitario=Decimal("50"),
        )
        self.linea_externo = LineaRepuesto.objects.create(
            documento=self.documento,
            origen_repuesto=ORIGEN_EXTERNO,
            codigo="EXT",
            nombre="Externo",
            cantidad=1,
            precio_unitario=Decimal("200"),
        )

    def test_validar_stock_disponible_pasa(self):
        errores = InventoryService.validar_stock_disponible(self.documento)
        assert errores == []

    def test_descontar_stock_bodega_y_desarme(self):
        InventoryService.procesar_movimiento_stock(self.documento, "descontar")
        self.repuesto.refresh_from_db()
        self.pieza.refresh_from_db()
        assert self.repuesto.cantidad_stock == 7
        assert self.pieza.cantidad == 3

    def test_externo_no_mueve_inventario(self):
        InventoryService.procesar_movimiento_stock(self.documento, "descontar")
        # repuesto y pieza ya descontados; EXTERNO no toca nada (no hay modelo para "externo")
        self.repuesto.refresh_from_db()
        self.pieza.refresh_from_db()
        assert self.repuesto.cantidad_stock == 7
        assert self.pieza.cantidad == 3

    def test_reponer_al_anular(self):
        InventoryService.procesar_movimiento_stock(self.documento, "descontar")
        self.repuesto.refresh_from_db()
        self.pieza.refresh_from_db()
        assert self.repuesto.cantidad_stock == 7
        assert self.pieza.cantidad == 3
        InventoryService.procesar_movimiento_stock(self.documento, "reponer")
        self.repuesto.refresh_from_db()
        self.pieza.refresh_from_db()
        assert self.repuesto.cantidad_stock == 10
        assert self.pieza.cantidad == 5
