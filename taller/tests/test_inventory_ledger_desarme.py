"""
Sprint D — inventory-ledger: integración EMISION/ANULACION para líneas DESARME.

21 tests:
  1.  Emisión DESARME crea MovimientoInventario con tipo=EMISION, cantidad_delta<0.
  2.  Anulación DESARME crea MovimientoInventario con tipo=ANULACION, cantidad_delta>0.
  3.  saldo_resultante coincide con PiezaDesarme.cantidad post-update.
  4.  Emisión exacta (cantidad==pieza.cantidad) cambia estado a VENDIDA.
  5.  Anulación desde VENDIDA restaura estado DISPONIBLE y activo=True.
  6.  Activo cambia a False cuando estado pasa a VENDIDA.
  7.  Metadata contiene estado_anterior, estado_resultante, activo_anterior, activo_resultante.
  8.  costo_unitario usa linea.costo_linea.
  9.  Dos líneas misma pieza encadenan saldo en memoria.
  10. Dos piezas distintas generan movimientos independientes.
  11. Segunda emisión idempotente: no duplica stock ni ledger.
  12. Segunda anulación idempotente: no duplica stock ni ledger.
  13. Idempotencia previa (key ya existe): no decrementa pieza ni crea nuevo ledger.
  14. Línea EXTERNO no genera ledger DESARME.
  15. Líneas STOCK_BODEGA siguen funcionando (regresión).
  16. Stock insuficiente lanza ValidationError y no crea movimiento.
  17. Error al crear ledger revierte cantidad y estado (atomicidad).
  18. Pieza UPDATE retorna 0 filas → no se crea ledger.
  19. Tenant isolation: empresa_b no ve movimientos de empresa_a.
  20. select_for_update solicitado para PiezaDesarme.
  21. VehiculoDesarme.estado_desarme = AGOTADO cuando todas las piezas se agotan.

Strategy:
  - Idempotency tests call procesar_movimiento_stock twice or pre-insert key manually.
  - select_for_update test patches PiezaDesarme.objects.select_for_update().
  - Rollback test patches MovimientoInventario.objects.create to raise IntegrityError;
    @transaction.atomic rolls back the pieza UPDATE.
  - VehiculoDesarme AGOTADO test verifies the estado_desarme update via DB read.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_DESARME,
    ORIGEN_EXTERNO,
    ORIGEN_STOCK_BODEGA,
)
from taller.models.movimiento_inventario import MovimientoInventario
from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE, ESTADO_VENDIDA
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.services.inventory_ledger_service import InventoryLedgerService
from taller.services.inventory_service import InventoryService
from taller.tests.factories import (
    DocumentoFactory,
    EmpresaFactory,
    RepuestoFactory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vehiculo(empresa, patente="D-001"):
    return VehiculoDesarme.objects.create(empresa=empresa, patente=patente)


def _make_pieza(empresa, *, vehiculo=None, cantidad=10, estado=ESTADO_DISPONIBLE, activo=True):
    if vehiculo is None:
        vehiculo = _make_vehiculo(empresa)
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        nombre="Pieza test",
        cantidad=cantidad,
        estado_pieza=estado,
        activo=activo,
    )


def _make_linea_desarme(doc, pieza, *, cantidad=1, costo_linea=None):
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre=pieza.nombre,
        codigo="PIEZA-TEST",
        cantidad=cantidad,
        precio_unitario=Decimal("5000"),
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_DESARME,
        pieza_desarme=pieza,
        costo_linea=costo_linea,
    )


def _make_linea_bodega(doc, repuesto, *, cantidad=1, costo_linea=None):
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre=repuesto.nombre,
        codigo=repuesto.part_number or "REP-TEST",
        cantidad=cantidad,
        precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_STOCK_BODEGA,
        repuesto=repuesto,
        costo_linea=costo_linea,
    )


# ---------------------------------------------------------------------------
# 1. Emisión DESARME crea MovimientoInventario con tipo=EMISION
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emision_desarme_crea_movimiento_tipo_emision():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=2)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    movimientos = MovimientoInventario.objects.filter(documento=doc)
    assert movimientos.count() == 1
    m = movimientos.first()
    assert m.tipo == MovimientoInventario.TipoMovimiento.EMISION
    assert m.cantidad_delta == -2
    assert m.origen_stock == MovimientoInventario.OrigenStock.DESARME


# ---------------------------------------------------------------------------
# 2. Anulación DESARME crea MovimientoInventario con tipo=ANULACION
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anulacion_desarme_crea_movimiento_tipo_anulacion():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=3)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _make_linea_desarme(doc, pieza, cantidad=2, costo_linea=Decimal("1000"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    movimientos = MovimientoInventario.objects.filter(documento=doc)
    assert movimientos.count() == 1
    m = movimientos.first()
    assert m.tipo == MovimientoInventario.TipoMovimiento.ANULACION
    assert m.cantidad_delta == 2
    assert m.origen_stock == MovimientoInventario.OrigenStock.DESARME


# ---------------------------------------------------------------------------
# 3. saldo_resultante coincide con PiezaDesarme.cantidad post-update
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_saldo_resultante_coincide_con_pieza_post_update():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    pieza.refresh_from_db()
    assert m.saldo_resultante == 7
    assert pieza.cantidad == 7


# ---------------------------------------------------------------------------
# 4. Emisión exacta cambia estado a VENDIDA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emision_exacta_cambia_estado_a_vendida():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=3)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.cantidad == 0
    assert pieza.estado_pieza == ESTADO_VENDIDA

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.saldo_resultante == 0
    assert m.metadata["estado_resultante"] == ESTADO_VENDIDA


# ---------------------------------------------------------------------------
# 5. Anulación desde VENDIDA restaura DISPONIBLE y activo=True
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anulacion_restaura_disponible_desde_vendida():
    empresa = EmpresaFactory(pais="CL")
    # Crear pieza en estado válido para poder crear la linea
    pieza = _make_pieza(empresa, cantidad=2, estado=ESTADO_DISPONIBLE, activo=True)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _make_linea_desarme(doc, pieza, cantidad=2, costo_linea=Decimal("500"))
    # Simular estado post-emisión: pieza quedó VENDIDA tras el descontar original
    PiezaDesarme.objects.filter(pk=pieza.pk).update(cantidad=0, estado_pieza=ESTADO_VENDIDA, activo=False)
    pieza.refresh_from_db()

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    pieza.refresh_from_db()
    assert pieza.cantidad == 2
    assert pieza.estado_pieza == ESTADO_DISPONIBLE
    assert pieza.activo is True

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.metadata["estado_resultante"] == ESTADO_DISPONIBLE
    assert m.metadata["activo_resultante"] is True


# ---------------------------------------------------------------------------
# 6. activo cambia a False cuando estado pasa a VENDIDA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_activo_false_cuando_estado_vendida():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=1, activo=True)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=1)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.activo is False
    assert pieza.estado_pieza == ESTADO_VENDIDA


# ---------------------------------------------------------------------------
# 7. Metadata contiene estados anterior/resultante
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_metadata_contiene_estados_anterior_y_resultante():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5, estado=ESTADO_DISPONIBLE, activo=True)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=2)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    meta = m.metadata
    assert meta["estado_anterior"] == ESTADO_DISPONIBLE
    assert meta["estado_resultante"] == ESTADO_DISPONIBLE
    assert meta["activo_anterior"] is True
    assert meta["activo_resultante"] is True
    assert meta["accion"] == "descontar"
    assert "inventory_ledger_version" in meta


# ---------------------------------------------------------------------------
# 8. costo_unitario usa linea.costo_linea
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_costo_unitario_usa_costo_linea():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _make_linea_desarme(doc, pieza, cantidad=1, costo_linea=Decimal("2500.00"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.costo_unitario == Decimal("2500.00")


# ---------------------------------------------------------------------------
# 9. Dos líneas misma pieza encadenan saldo en memoria
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dos_lineas_misma_pieza_encadenan_saldo():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=3)
    _make_linea_desarme(doc, pieza, cantidad=4)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.cantidad == 3  # 10 - 3 - 4

    movimientos = MovimientoInventario.objects.filter(documento=doc).order_by("pk")
    assert movimientos.count() == 2
    assert movimientos[0].saldo_resultante == 7   # 10 - 3
    assert movimientos[1].saldo_resultante == 3   # 7 - 4


# ---------------------------------------------------------------------------
# 10. Dos piezas distintas generan movimientos independientes
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dos_piezas_generan_movimientos_independientes():
    empresa = EmpresaFactory(pais="CL")
    pieza_a = _make_pieza(empresa, cantidad=5)
    pieza_b = _make_pieza(empresa, cantidad=8)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza_a, cantidad=2)
    _make_linea_desarme(doc, pieza_b, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza_a.refresh_from_db()
    pieza_b.refresh_from_db()
    assert pieza_a.cantidad == 3
    assert pieza_b.cantidad == 5

    assert MovimientoInventario.objects.filter(documento=doc).count() == 2
    assert MovimientoInventario.objects.filter(pieza_desarme=pieza_a).count() == 1
    assert MovimientoInventario.objects.filter(pieza_desarme=pieza_b).count() == 1


# ---------------------------------------------------------------------------
# 11. Segunda emisión idempotente: no duplica stock ni ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_segunda_emision_idempotente():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=2)

    InventoryService.procesar_movimiento_stock(doc, "descontar")
    # Segunda llamada — misma clave, no debe duplicar
    InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.cantidad == 3  # solo se aplicó una vez
    assert MovimientoInventario.objects.filter(documento=doc).count() == 1


# ---------------------------------------------------------------------------
# 12. Segunda anulación idempotente: no duplica stock ni ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_segunda_anulacion_idempotente():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=3)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _make_linea_desarme(doc, pieza, cantidad=2, costo_linea=Decimal("100"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")
    InventoryService.procesar_movimiento_stock(doc, "reponer")

    pieza.refresh_from_db()
    assert pieza.cantidad == 5  # 3 + 2, solo una vez
    assert MovimientoInventario.objects.filter(documento=doc).count() == 1


# ---------------------------------------------------------------------------
# 13. Key preexistente no decrementa pieza ni crea nuevo ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_idempotencia_previa_no_duplica_stock():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea_desarme(doc, pieza, cantidad=2)

    # Insertar manualmente el MovimientoInventario con la clave que generaría el servicio
    key = InventoryLedgerService.build_idempotency_key(
        empresa_id=empresa.pk,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.DESARME,
        repuesto_id=None,
        pieza_desarme_id=pieza.pk,
        documento_id=doc.pk,
        linea_repuesto_id=linea.pk,
        cantidad_delta=-2,
    )
    MovimientoInventario.objects.create(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.DESARME,
        pieza_desarme=pieza,
        documento=doc,
        linea_repuesto=linea,
        cantidad_delta=-2,
        saldo_resultante=3,
        idempotency_key=key,
    )

    # La llamada al servicio debe detectar la key y omitir el UPDATE
    InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.cantidad == 5  # sin cambio
    assert MovimientoInventario.objects.filter(documento=doc).count() == 1


# ---------------------------------------------------------------------------
# 14. Línea EXTERNO no genera ledger DESARME
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_externo_no_genera_ledger_desarme():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    LineaRepuesto.objects.create(
        documento=doc,
        nombre="Mano de obra",
        codigo="MO-1",
        cantidad=1,
        precio_unitario=Decimal("5000"),
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_EXTERNO,
        repuesto=None,
    )

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 15. STOCK_BODEGA sigue funcionando (regresión)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_stock_bodega_regresion():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=8)
    pieza = _make_pieza(empresa, cantidad=6)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=3)
    _make_linea_desarme(doc, pieza, cantidad=2)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    repuesto.refresh_from_db()
    pieza.refresh_from_db()
    assert repuesto.cantidad_stock == 5
    assert pieza.cantidad == 4

    assert MovimientoInventario.objects.filter(documento=doc, origen_stock="STOCK_BODEGA").count() == 1
    assert MovimientoInventario.objects.filter(documento=doc, origen_stock="DESARME").count() == 1


# ---------------------------------------------------------------------------
# 16. Stock insuficiente lanza ValidationError y no crea movimiento
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_stock_insuficiente_lanza_error():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea_desarme(doc, pieza, cantidad=1)
    # Reducir stock de pieza post-creación para crear escenario insuficiente
    PiezaDesarme.objects.filter(pk=pieza.pk).update(cantidad=1)
    # Escalar la línea por encima del stock disponible
    LineaRepuesto.objects.filter(pk=linea.pk).update(cantidad=5)

    with pytest.raises(ValidationError, match="Stock insuficiente"):
        InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.cantidad == 1  # sin cambio
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 17. Error al crear ledger revierte cantidad y estado (atomicidad)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_error_ledger_revierte_cantidad_y_estado():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=2)

    original_create = MovimientoInventario.objects.create

    call_count = {"n": 0}

    def fail_create(**kwargs):
        if kwargs.get("origen_stock") == MovimientoInventario.OrigenStock.DESARME:
            raise IntegrityError("simulated ledger failure")
        return original_create(**kwargs)

    with patch.object(MovimientoInventario.objects, "create", side_effect=fail_create):
        with pytest.raises((IntegrityError, Exception)):
            InventoryService.procesar_movimiento_stock(doc, "descontar")

    pieza.refresh_from_db()
    assert pieza.cantidad == 5  # rolled back
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 18. Pieza UPDATE retorna 0 filas → no se crea ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_pieza_update_cero_filas_no_crea_ledger():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=2)

    original_filter = PiezaDesarme.objects.filter

    call_count = {"update_calls": 0}

    def fake_filter(*args, **kwargs):
        qs = original_filter(*args, **kwargs)
        pk_val = kwargs.get("id")
        if pk_val == pieza.pk and "empresa" in kwargs:
            mock_qs = MagicMock()
            mock_qs.update.return_value = 0
            call_count["update_calls"] += 1
            return mock_qs
        return qs

    with patch.object(PiezaDesarme.objects, "filter", side_effect=fake_filter):
        InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert call_count["update_calls"] >= 1
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 19. Tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tenant_isolation():
    empresa_a = EmpresaFactory(pais="CL")
    empresa_b = EmpresaFactory(pais="CL")
    pieza_a = _make_pieza(empresa_a, cantidad=5)
    pieza_b = _make_pieza(empresa_b, cantidad=5)
    doc_a = DocumentoFactory(empresa=empresa_a, tipo="OT", estado="BORRADOR")
    doc_b = DocumentoFactory(empresa=empresa_b, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc_a, pieza_a, cantidad=2)
    _make_linea_desarme(doc_b, pieza_b, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc_a, "descontar")
    InventoryService.procesar_movimiento_stock(doc_b, "descontar")

    assert MovimientoInventario.objects.filter(empresa=empresa_a).count() == 1
    assert MovimientoInventario.objects.filter(empresa=empresa_b).count() == 1

    m_a = MovimientoInventario.objects.get(empresa=empresa_a)
    m_b = MovimientoInventario.objects.get(empresa=empresa_b)
    assert m_a.pieza_desarme_id == pieza_a.pk
    assert m_b.pieza_desarme_id == pieza_b.pk


# ---------------------------------------------------------------------------
# 20. select_for_update solicitado para PiezaDesarme
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_select_for_update_solicitado_para_pieza():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza, cantidad=1)

    real_qs = PiezaDesarme.objects.filter(id__in=[pieza.pk]).order_by("pk")
    mock_sfu = MagicMock(return_value=real_qs)

    with patch.object(
        PiezaDesarme.objects.__class__,
        "select_for_update",
        mock_sfu,
    ):
        with patch.object(PiezaDesarme.objects, "select_for_update", mock_sfu):
            InventoryService.procesar_movimiento_stock(doc, "descontar")

    mock_sfu.assert_called()


# ---------------------------------------------------------------------------
# 21. VehiculoDesarme.estado_desarme = AGOTADO cuando todas las piezas se agotan
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_vehiculo_estado_agotado_cuando_todas_piezas_se_agotan():
    empresa = EmpresaFactory(pais="CL")
    veh = _make_vehiculo(empresa, patente="AG-001")

    pieza_a = PiezaDesarme.objects.create(
        empresa=empresa, vehiculo_desarme=veh, nombre="Pieza A", codigo="PA-001",
        cantidad=1, estado_pieza=ESTADO_DISPONIBLE, activo=True,
    )
    pieza_b = PiezaDesarme.objects.create(
        empresa=empresa, vehiculo_desarme=veh, nombre="Pieza B", codigo="PA-002",
        cantidad=2, estado_pieza=ESTADO_DISPONIBLE, activo=True,
    )

    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea_desarme(doc, pieza_a, cantidad=1)  # agotará pieza_a (→ VENDIDA)
    _make_linea_desarme(doc, pieza_b, cantidad=2)  # agotará pieza_b (→ VENDIDA)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    veh.refresh_from_db()
    assert veh.estado_desarme == "AGOTADO"
