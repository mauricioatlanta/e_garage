"""
Sprint C — inventory-ledger: integración EMISION/ANULACION STOCK_BODEGA.

22 tests:
  1.  EMISION STOCK_BODEGA crea MovimientoInventario con tipo=EMISION.
  2.  ANULACION STOCK_BODEGA crea MovimientoInventario con tipo=ANULACION.
  3.  EMISION: saldo_resultante = stock_inicial - cantidad.
  4.  ANULACION: saldo_resultante = stock_inicial + cantidad.
  5.  EMISION actualiza Repuesto.cantidad_stock.
  6.  ANULACION restaura Repuesto.cantidad_stock.
  7.  Una línea → exactamente un MovimientoInventario.
  8.  Dos líneas mismo repuesto → saldo encadenado en memoria.
  9.  Dos líneas repuestos distintos → un movimiento por línea.
  10. costo_unitario usa costo_linea congelado en la misma transacción.
  11. costo_unitario es None cuando precio_compra es None.
  12. Línea DESARME no crea MovimientoInventario.
  13. Línea EXTERNO no crea MovimientoInventario.
  14. Tipo PRES no crea MovimientoInventario.
  15. idempotency_key presente y con 64 chars (SHA-256).
  16. record_stock_movement idempotente: segunda llamada devuelve (existing, False).
  17. select_for_update llamado para STOCK_BODEGA (servicio).
  18. select_for_update NO llamado sin líneas STOCK_BODEGA.
  19. metadata contiene campos obligatorios.
  20. Rollback atómico: si ledger falla, stock no se modifica.
  21. accion=ajustar no crea MovimientoInventario.
  22. origen_stock del movimiento es STOCK_BODEGA.

Strategy:
  - select_for_update tests mock Repuesto.objects.select_for_update
    y devuelven un queryset real para que el dict-comprehension funcione.
  - Rollback test: mock record_stock_movement lanza ValueError dentro del
    @transaction.atomic → savepoint revierte F()-update → stock sin cambio.
  - Los tests de lock del servicio son independientes de los tests de lock
    de la vista (Sprint A).
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_DESARME,
    ORIGEN_EXTERNO,
    ORIGEN_STOCK_BODEGA,
)
from taller.models.movimiento_inventario import MovimientoInventario
from taller.models.repuesto import Repuesto
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

def _make_linea_bodega(doc, repuesto, *, cantidad=1, costo_linea=None):
    linea = LineaRepuesto.objects.create(
        documento=doc,
        nombre=repuesto.nombre,
        codigo=repuesto.part_number or "TEST",
        cantidad=cantidad,
        precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_STOCK_BODEGA,
        repuesto=repuesto,
        costo_linea=costo_linea,
    )
    return linea


def _make_linea_externo(doc):
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre="Mano de obra",
        codigo="MO-1",
        cantidad=1,
        precio_unitario=Decimal("5000"),
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_EXTERNO,
        repuesto=None,
    )


def _make_pieza(empresa):
    from taller.models.vehiculo_desarme import VehiculoDesarme
    from taller.models.pieza_desarme import PiezaDesarme

    veh = VehiculoDesarme.objects.create(empresa=empresa, patente="DS-TST")
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=veh,
        nombre="Pieza test",
        cantidad=10,
    )


# ---------------------------------------------------------------------------
# 1. EMISION STOCK_BODEGA crea MovimientoInventario con tipo=EMISION
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emision_bodega_crea_movimiento_tipo_emision():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=2)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    movimientos = MovimientoInventario.objects.filter(documento=doc)
    assert movimientos.count() == 1
    assert movimientos.first().tipo == MovimientoInventario.TipoMovimiento.EMISION


# ---------------------------------------------------------------------------
# 2. ANULACION STOCK_BODEGA crea MovimientoInventario con tipo=ANULACION
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anulacion_bodega_crea_movimiento_tipo_anulacion():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    _make_linea_bodega(doc, repuesto, cantidad=2, costo_linea=Decimal("1500"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    movimientos = MovimientoInventario.objects.filter(documento=doc)
    assert movimientos.count() == 1
    assert movimientos.first().tipo == MovimientoInventario.TipoMovimiento.ANULACION


# ---------------------------------------------------------------------------
# 3. EMISION: saldo_resultante = stock_inicial - cantidad
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emision_saldo_resultante_correcto():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.cantidad_delta == -3
    assert m.saldo_resultante == 7  # 10 - 3


# ---------------------------------------------------------------------------
# 4. ANULACION: saldo_resultante = stock_inicial + cantidad
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anulacion_saldo_resultante_correcto():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=3)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    _make_linea_bodega(doc, repuesto, cantidad=2, costo_linea=Decimal("1000"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.cantidad_delta == 2
    assert m.saldo_resultante == 5  # 3 + 2


# ---------------------------------------------------------------------------
# 5. EMISION actualiza Repuesto.cantidad_stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emision_actualiza_cantidad_stock_repuesto():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=8)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 5


# ---------------------------------------------------------------------------
# 6. ANULACION restaura Repuesto.cantidad_stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anulacion_restaura_cantidad_stock_repuesto():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=2)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    _make_linea_bodega(doc, repuesto, cantidad=3, costo_linea=Decimal("500"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 5  # 2 + 3


# ---------------------------------------------------------------------------
# 7. Una línea → exactamente un MovimientoInventario
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_una_linea_crea_exactamente_un_movimiento():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=1)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert MovimientoInventario.objects.filter(documento=doc).count() == 1


# ---------------------------------------------------------------------------
# 8. Dos líneas mismo repuesto → saldo encadenado
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dos_lineas_mismo_repuesto_encadenan_saldo():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=3)
    _make_linea_bodega(doc, repuesto, cantidad=4)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    movimientos = list(
        MovimientoInventario.objects.filter(documento=doc).order_by("pk")
    )
    assert len(movimientos) == 2

    # Saldo encadenado: primer movimiento aplica sobre 10, segundo sobre 7
    assert movimientos[0].cantidad_delta == -3
    assert movimientos[0].saldo_resultante == 7

    assert movimientos[1].cantidad_delta == -4
    assert movimientos[1].saldo_resultante == 3

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 3


# ---------------------------------------------------------------------------
# 9. Dos líneas repuestos distintos → un movimiento por línea
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dos_lineas_repuestos_distintos_un_movimiento_cada_una():
    empresa = EmpresaFactory(pais="CL")
    rep_a = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    rep_b = RepuestoFactory(empresa=empresa, cantidad_stock=20)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, rep_a, cantidad=2)
    _make_linea_bodega(doc, rep_b, cantidad=5)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert MovimientoInventario.objects.filter(documento=doc, repuesto=rep_a).count() == 1
    assert MovimientoInventario.objects.filter(documento=doc, repuesto=rep_b).count() == 1

    rep_a.refresh_from_db()
    rep_b.refresh_from_db()
    assert rep_a.cantidad_stock == 8
    assert rep_b.cantidad_stock == 15


# ---------------------------------------------------------------------------
# 10. costo_unitario usa costo_linea congelado en la misma transacción
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_costo_unitario_usa_costo_linea_congelado():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    repuesto.precio_compra = Decimal("2500.00")
    repuesto.save()

    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=1)  # costo_linea=None → se congela

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.costo_unitario == Decimal("2500.00")


# ---------------------------------------------------------------------------
# 11. costo_unitario usa costo_linea preexistente sin consultar precio_compra
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_costo_unitario_usa_costo_linea_preexistente_en_anulacion():
    """
    En ANULACION (reponer), costo_linea ya fue congelado en la EMISION previa.
    El servicio no lo sobreescribe; record_stock_movement lo pasa tal cual
    como costo_unitario, sin consultar repuesto.precio_compra.
    """
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=3)
    repuesto.precio_compra = Decimal("9999.00")  # distinto al costo congelado
    repuesto.save()

    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    # costo_linea ya seteado (como si hubiera sido congelado en la EMISION previa)
    linea = _make_linea_bodega(doc, repuesto, cantidad=2, costo_linea=Decimal("1234.00"))

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    m = MovimientoInventario.objects.get(documento=doc)
    # Debe usar costo_linea=1234, NO precio_compra=9999
    assert m.costo_unitario == Decimal("1234.00")


# ---------------------------------------------------------------------------
# 12. Línea DESARME no crea MovimientoInventario
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_linea_desarme_no_crea_movimiento_inventario():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    LineaRepuesto.objects.create(
        documento=doc,
        nombre=pieza.nombre,
        codigo="DS-1",
        cantidad=1,
        precio_unitario=Decimal("5000"),
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_DESARME,
        pieza_desarme=pieza,
    )

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 13. Línea EXTERNO no crea MovimientoInventario
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_linea_externo_no_crea_movimiento_inventario():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_externo(doc)

    resultado = InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert resultado["procesado"] is False
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 14. Tipo PRES no crea MovimientoInventario
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tipo_pres_no_crea_movimiento_inventario():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="PRES", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=1)

    resultado = InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert resultado["procesado"] is False
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 15. idempotency_key tiene 64 caracteres (SHA-256 hexdigest)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_idempotency_key_tiene_64_chars():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=1)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    assert len(m.idempotency_key) == 64


# ---------------------------------------------------------------------------
# 16. record_stock_movement idempotente: segunda llamada devuelve (existing, False)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_record_stock_movement_idempotente():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    linea = _make_linea_bodega(doc, repuesto, cantidad=2)

    args = dict(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        repuesto=repuesto,
        documento=doc,
        linea_repuesto=linea,
        cantidad_delta=-2,
        saldo_resultante=8,
        costo_unitario=None,
    )

    m1, created1 = InventoryLedgerService.record_stock_movement(**args)
    m2, created2 = InventoryLedgerService.record_stock_movement(**args)

    assert created1 is True
    assert created2 is False
    assert m1.pk == m2.pk
    assert MovimientoInventario.objects.filter(documento=doc).count() == 1


# ---------------------------------------------------------------------------
# 17. select_for_update llamado para STOCK_BODEGA (nivel servicio)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_select_for_update_llamado_en_bodega_servicio():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=2)

    # Return the real queryset so the dict-comprehension inside the service works
    real_qs = Repuesto.objects.filter(pk=repuesto.pk)
    sfu_qs = MagicMock()
    sfu_qs.filter.return_value = sfu_qs
    sfu_qs.order_by.return_value = real_qs

    with patch.object(Repuesto.objects, "select_for_update", return_value=sfu_qs) as mock_sfu:
        with patch.object(InventoryLedgerService, "record_stock_movement", return_value=(MagicMock(), True)):
            InventoryService.procesar_movimiento_stock(doc, "descontar")

    mock_sfu.assert_called_once()


# ---------------------------------------------------------------------------
# 18. select_for_update NO llamado sin líneas STOCK_BODEGA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_no_select_for_update_sin_lineas_bodega():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_externo(doc)

    with patch.object(Repuesto.objects, "select_for_update") as mock_sfu:
        InventoryService.procesar_movimiento_stock(doc, "descontar")

    mock_sfu.assert_not_called()


# ---------------------------------------------------------------------------
# 19. metadata contiene campos obligatorios
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_metadata_contiene_campos_obligatorios():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=1)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.metadata.get("inventory_ledger_version") == InventoryLedgerService.HASH_VERSION
    assert m.metadata.get("documento_tipo") == doc.tipo
    assert m.metadata.get("accion") == "descontar"
    assert "documento_estado" in m.metadata


# ---------------------------------------------------------------------------
# 20. Rollback atómico: si ledger falla, stock no se modifica
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rollback_atomico_si_ledger_falla():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=2)

    with patch.object(
        InventoryLedgerService,
        "record_stock_movement",
        side_effect=ValueError("ledger error simulado"),
    ):
        with pytest.raises(ValueError, match="ledger error simulado"):
            InventoryService.procesar_movimiento_stock(doc, "descontar")

    # El F()-update sobre Repuesto debe haber sido revertido por el savepoint
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 5
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 21. accion=ajustar no crea MovimientoInventario
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ajustar_no_crea_movimiento_inventario():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    # línea con cantidad=4; cantidad anterior=2; diferencia=2; delta=-2
    linea = _make_linea_bodega(doc, repuesto, cantidad=4)

    InventoryService.procesar_movimiento_stock(doc, "ajustar", {linea.id: 2})

    assert MovimientoInventario.objects.filter(documento=doc).count() == 0
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 3  # 5 - 2


# ---------------------------------------------------------------------------
# 22. origen_stock del movimiento creado es STOCK_BODEGA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_origen_stock_bodega_en_movimiento_creado():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea_bodega(doc, repuesto, cantidad=1)

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.origen_stock == MovimientoInventario.OrigenStock.STOCK_BODEGA
    assert m.repuesto_id == repuesto.pk
    assert m.pieza_desarme_id is None
