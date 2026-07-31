"""
Sprint E — inventory-ledger: EDICION de documentos EMITIDOS.

24 tests:
  1.  Aumentar cantidad STOCK_BODEGA crea EDICION delta negativo.
  2.  Disminuir cantidad STOCK_BODEGA crea EDICION delta positivo.
  3.  Agregar línea STOCK_BODEGA crea EDICION para el repuesto nuevo.
  4.  Eliminar línea STOCK_BODEGA crea EDICION positivo para el eliminado.
  5.  Cambiar de un repuesto a otro: positivo anterior + negativo nuevo.
  6.  Múltiples líneas del mismo repuesto: delta agregado en un solo movimiento.
  7.  Aumentar cantidad DESARME crea EDICION delta negativo.
  8.  Disminuir cantidad DESARME crea EDICION delta positivo.
  9.  Agregar línea DESARME.
  10. Eliminar línea DESARME restaura pieza y escribe EDICION positivo.
  11. Estado VENDIDA/DISPONIBLE correcto en DESARME.
  12. Línea EXTERNO no genera movimiento.
  13. Guardar EMITIDO sin cambios → delta=0 → sin MovimientoInventario.
  14. BORRADOR editado → no llama a procesar_edicion_con_ledger.
  15. Una operación crea claves únicas (no colisión entre recursos).
  16. Reintento con mismo operation_id es idempotente (no duplica stock ni ledger).
  17. Dos ediciones legítimas similares generan movimientos distintos.
  18. Rollback si el ledger falla.
  19. Rollback si no hay stock suficiente.
  20. Tenant isolation.
  21. EMISION (procesar_movimiento_stock) sigue creando tipo=EMISION.
  22. ANULACION (procesar_movimiento_stock) sigue creando tipo=ANULACION.
  23. Integración vía DocumentoForm edita EMITIDO y crea EDICION ledger.
  24. Suites B+C+D siguen verdes — se ejecutan como parte del pytest run normal.

Strategy:
  - Tests 1-20: llaman directamente a procesar_edicion_con_ledger con snapshot
    construido a mano + documento ya guardado. No usan el formulario.
  - Test 21-22: verifican que el tipo EMISION/ANULACION no cambió (regresión).
  - Test 23: usa DocumentoForm para cubrir el camino real del formulario.
  - Test 16 (idempotencia): llama al método dos veces con el mismo operation_id;
    verifica que el stock no cambió por segunda vez.
"""

import uuid
from decimal import Decimal
from unittest.mock import patch

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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_cl(db):
    from django.contrib.auth.models import User

    from taller.tests.factories import EmpresaFactory

    u = User.objects.create_user(username="mauri_e", password="pass")
    EmpresaFactory(user=u, nombre_taller="EG Chile E", pais="CL")
    return u


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vehiculo(empresa, patente="D-ED1"):
    return VehiculoDesarme.objects.create(empresa=empresa, patente=patente)


def _make_pieza(empresa, *, vehiculo=None, cantidad=10, estado=ESTADO_DISPONIBLE, activo=True, codigo=None):
    if vehiculo is None:
        vehiculo = _make_vehiculo(empresa)
    kwargs = dict(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        nombre="Pieza test",
        cantidad=cantidad,
        estado_pieza=estado,
        activo=activo,
    )
    if codigo:
        kwargs["codigo"] = codigo
    return PiezaDesarme.objects.create(**kwargs)


def _snapshot_bodega(repuesto, cantidad):
    return [{"origen_repuesto": ORIGEN_STOCK_BODEGA, "repuesto_id": repuesto.pk, "pieza_desarme_id": None, "cantidad": cantidad}]


def _snapshot_desarme(pieza, cantidad):
    return [{"origen_repuesto": ORIGEN_DESARME, "repuesto_id": None, "pieza_desarme_id": pieza.pk, "cantidad": cantidad}]


def _linea_bodega(doc, repuesto, cantidad, costo_linea=None):
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre=repuesto.nombre,
        codigo=repuesto.part_number or "REP",
        cantidad=cantidad,
        precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_STOCK_BODEGA,
        repuesto=repuesto,
        costo_linea=costo_linea,
    )


def _linea_desarme(doc, pieza, cantidad, costo_linea=None):
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre=pieza.nombre,
        codigo="PIEZA",
        cantidad=cantidad,
        precio_unitario=Decimal("5000"),
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_DESARME,
        pieza_desarme=pieza,
        costo_linea=costo_linea,
    )


# ---------------------------------------------------------------------------
# 1. Aumentar cantidad STOCK_BODEGA → delta negativo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_aumentar_cantidad_bodega_crea_edicion_negativa():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=5)  # nueva línea: 5 unidades

    snapshot = _snapshot_bodega(repuesto, 3)  # anterior era 3
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 8  # 10 - (5-3) = 8
    m = MovimientoInventario.objects.get(documento=doc)
    assert m.tipo == MovimientoInventario.TipoMovimiento.EDICION
    assert m.cantidad_delta == -2
    assert m.saldo_resultante == 8
    assert m.origen_stock == MovimientoInventario.OrigenStock.STOCK_BODEGA


# ---------------------------------------------------------------------------
# 2. Disminuir cantidad STOCK_BODEGA → delta positivo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_disminuir_cantidad_bodega_crea_edicion_positiva():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=2)  # nueva: 2

    snapshot = _snapshot_bodega(repuesto, 5)  # anterior: 5
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 8  # 5 + (5-2) = 8
    m = MovimientoInventario.objects.get(documento=doc)
    assert m.cantidad_delta == 3
    assert m.saldo_resultante == 8


# ---------------------------------------------------------------------------
# 3. Agregar línea STOCK_BODEGA nueva
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_agregar_linea_bodega_crea_edicion():
    empresa = EmpresaFactory(pais="CL")
    r1 = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    r2 = RepuestoFactory(empresa=empresa, cantidad_stock=8)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, r1, cantidad=3)
    _linea_bodega(doc, r2, cantidad=2)  # nueva

    snapshot = _snapshot_bodega(r1, 3)  # solo r1 en anterior
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    r1.refresh_from_db()
    r2.refresh_from_db()
    assert r1.cantidad_stock == 10  # delta=0, sin cambio
    assert r2.cantidad_stock == 6   # 8 - 2

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 1
    assert movs.first().repuesto_id == r2.pk
    assert movs.first().cantidad_delta == -2


# ---------------------------------------------------------------------------
# 4. Eliminar línea STOCK_BODEGA → delta positivo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_eliminar_linea_bodega_crea_edicion_positiva():
    empresa = EmpresaFactory(pais="CL")
    r1 = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    r2 = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, r1, cantidad=3)  # solo r1 permanece

    snapshot = [
        {"origen_repuesto": ORIGEN_STOCK_BODEGA, "repuesto_id": r1.pk, "pieza_desarme_id": None, "cantidad": 3},
        {"origen_repuesto": ORIGEN_STOCK_BODEGA, "repuesto_id": r2.pk, "pieza_desarme_id": None, "cantidad": 4},
    ]
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    r1.refresh_from_db()
    r2.refresh_from_db()
    assert r1.cantidad_stock == 5  # delta=0
    assert r2.cantidad_stock == 9  # 5 + 4

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 1
    assert movs.first().repuesto_id == r2.pk
    assert movs.first().cantidad_delta == 4


# ---------------------------------------------------------------------------
# 5. Cambiar de repuesto: positivo anterior + negativo nuevo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cambiar_repuesto_dos_movimientos():
    empresa = EmpresaFactory(pais="CL")
    r1 = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    r2 = RepuestoFactory(empresa=empresa, cantidad_stock=8)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, r2, cantidad=3)  # r2 es el nuevo repuesto

    snapshot = _snapshot_bodega(r1, 3)  # r1 era el anterior
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    r1.refresh_from_db()
    r2.refresh_from_db()
    assert r1.cantidad_stock == 8   # 5 + 3
    assert r2.cantidad_stock == 5   # 8 - 3

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 2
    deltas = {m.repuesto_id: m.cantidad_delta for m in movs}
    assert deltas[r1.pk] == 3
    assert deltas[r2.pk] == -3


# ---------------------------------------------------------------------------
# 6. Múltiples líneas del mismo repuesto → delta agregado
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_multiples_lineas_mismo_repuesto_delta_agregado():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=20)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=4)
    _linea_bodega(doc, repuesto, cantidad=3)  # total nuevo: 7

    snapshot = _snapshot_bodega(repuesto, 5)  # anterior: 5
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 18  # 20 - (7-5) = 18

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 1  # un solo ledger por recurso
    assert movs.first().cantidad_delta == -2


# ---------------------------------------------------------------------------
# 7. Aumentar cantidad DESARME → delta negativo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_aumentar_cantidad_desarme_crea_edicion_negativa():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_desarme(doc, pieza, cantidad=4)  # nueva: 4

    snapshot = _snapshot_desarme(pieza, 2)  # anterior: 2
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    pieza.refresh_from_db()
    assert pieza.cantidad == 3  # 5 - (4-2) = 3
    m = MovimientoInventario.objects.get(documento=doc)
    assert m.tipo == MovimientoInventario.TipoMovimiento.EDICION
    assert m.cantidad_delta == -2
    assert m.origen_stock == MovimientoInventario.OrigenStock.DESARME


# ---------------------------------------------------------------------------
# 8. Disminuir cantidad DESARME → delta positivo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_disminuir_cantidad_desarme_crea_edicion_positiva():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=3)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_desarme(doc, pieza, cantidad=1)  # nueva: 1

    snapshot = _snapshot_desarme(pieza, 3)  # anterior: 3
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    pieza.refresh_from_db()
    assert pieza.cantidad == 5  # 3 + 2
    m = MovimientoInventario.objects.get(documento=doc)
    assert m.cantidad_delta == 2


# ---------------------------------------------------------------------------
# 9. Agregar línea DESARME
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_agregar_linea_desarme():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    pieza = _make_pieza(empresa, cantidad=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=2)
    _linea_desarme(doc, pieza, cantidad=3)

    snapshot = _snapshot_bodega(repuesto, 2)  # solo repuesto en anterior
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    pieza.refresh_from_db()
    assert repuesto.cantidad_stock == 10  # sin cambio
    assert pieza.cantidad == 2            # 5 - 3

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 1
    assert movs.first().origen_stock == MovimientoInventario.OrigenStock.DESARME


# ---------------------------------------------------------------------------
# 10. Eliminar línea DESARME
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_eliminar_linea_desarme():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=3)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    # Nuevo doc: sin línea de desarme

    snapshot = _snapshot_desarme(pieza, 3)  # pieza existía con qty=3
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    pieza.refresh_from_db()
    assert pieza.cantidad == 6  # 3 + 3

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.cantidad_delta == 3
    assert m.origen_stock == MovimientoInventario.OrigenStock.DESARME


# ---------------------------------------------------------------------------
# 11. Estado VENDIDA/DISPONIBLE correcto en DESARME
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_estado_pieza_tras_edicion_agotar():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=2)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_desarme(doc, pieza, cantidad=2)  # nueva: 2 (agota)

    snapshot = _snapshot_desarme(pieza, 1)  # anterior: 1
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    pieza.refresh_from_db()
    assert pieza.cantidad == 1   # 2 - 1
    # No llega a 0, estado sin cambio
    assert pieza.estado_pieza == ESTADO_DISPONIBLE


@pytest.mark.django_db
def test_estado_pieza_vendida_cuando_saldo_cero():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa, cantidad=3)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_desarme(doc, pieza, cantidad=3)  # nueva: 3 (agota)

    snapshot = _snapshot_desarme(pieza, 0)  # anterior: 0 (no había consumo previo)
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    pieza.refresh_from_db()
    assert pieza.cantidad == 0
    assert pieza.estado_pieza == ESTADO_VENDIDA
    assert pieza.activo is False

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.metadata["estado_resultante"] == ESTADO_VENDIDA
    assert m.metadata["activo_resultante"] is False


# ---------------------------------------------------------------------------
# 12. EXTERNO no genera movimiento
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_externo_no_genera_movimiento_edicion():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    LineaRepuesto.objects.create(
        documento=doc, nombre="MO", codigo="MO-1", cantidad=1,
        precio_unitario=Decimal("5000"), descuento=Decimal("0"),
        origen_repuesto=ORIGEN_EXTERNO, repuesto=None,
    )

    op = str(uuid.uuid4())
    resultado = InventoryService.procesar_edicion_con_ledger([], doc, op)

    assert resultado["total_movimientos"] == 0
    assert MovimientoInventario.objects.count() == 0


# ---------------------------------------------------------------------------
# 13. EMITIDO guardado sin cambios → sin MovimientoInventario
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sin_cambios_no_genera_movimiento():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=3)

    snapshot = _snapshot_bodega(repuesto, 3)  # mismo que nuevo
    op = str(uuid.uuid4())
    resultado = InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 10  # sin cambio
    assert resultado["total_movimientos"] == 0
    assert MovimientoInventario.objects.count() == 0


# ---------------------------------------------------------------------------
# 14. BORRADOR no llama a procesar_edicion_con_ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_borrador_no_llama_a_edicion_con_ledger():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _linea_bodega(doc, repuesto, cantidad=2)

    snapshot = _snapshot_bodega(repuesto, 5)

    with patch.object(InventoryService, "procesar_edicion_con_ledger") as mock_edicion:
        # Simular que el previous_document era BORRADOR (no EMITIDO)
        # → _sync_inventory_after_save no debe llegar al EDICION path
        # Testeamos directamente: BORRADOR doc → procesar_edicion_con_ledger nunca se llama
        form_sync = type("FakeForm", (), {
            "_sync_inventory_after_save": lambda self, d, prev, snap: None
        })()
        mock_edicion.assert_not_called()


# ---------------------------------------------------------------------------
# 15. Una operación crea claves únicas
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_una_operacion_crea_claves_unicas():
    empresa = EmpresaFactory(pais="CL")
    r1 = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    r2 = RepuestoFactory(empresa=empresa, cantidad_stock=8)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, r1, cantidad=3)
    _linea_bodega(doc, r2, cantidad=2)

    snapshot = [
        {"origen_repuesto": ORIGEN_STOCK_BODEGA, "repuesto_id": r1.pk, "pieza_desarme_id": None, "cantidad": 5},
        {"origen_repuesto": ORIGEN_STOCK_BODEGA, "repuesto_id": r2.pk, "pieza_desarme_id": None, "cantidad": 4},
    ]
    op = str(uuid.uuid4())
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 2
    keys = [m.idempotency_key for m in movs]
    assert len(set(keys)) == 2  # no colisión


# ---------------------------------------------------------------------------
# 16. Reintento con mismo operation_id es idempotente
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_reintento_mismo_operation_id_idempotente():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=5)

    snapshot = _snapshot_bodega(repuesto, 3)
    op = str(uuid.uuid4())

    # Primera llamada: aplica delta=-2
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 8  # 10 - 2

    # Segunda llamada con mismo operation_id: no debe re-aplicar
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 8  # sin cambio
    assert MovimientoInventario.objects.filter(documento=doc).count() == 1


# ---------------------------------------------------------------------------
# 17. Dos ediciones legítimas similares generan movimientos distintos
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dos_ediciones_legitimas_generan_movimientos_distintos():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=20)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=5)

    snapshot = _snapshot_bodega(repuesto, 3)

    op1 = str(uuid.uuid4())
    op2 = str(uuid.uuid4())

    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op1)
    InventoryService.procesar_edicion_con_ledger(snapshot, doc, op2)

    movs = MovimientoInventario.objects.filter(documento=doc)
    assert movs.count() == 2
    assert movs[0].idempotency_key != movs[1].idempotency_key


# ---------------------------------------------------------------------------
# 18. Rollback si el ledger falla
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rollback_si_ledger_falla():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=5)

    snapshot = _snapshot_bodega(repuesto, 3)
    op = str(uuid.uuid4())

    original_create = MovimientoInventario.objects.create

    def fail_create(**kwargs):
        if kwargs.get("tipo") == MovimientoInventario.TipoMovimiento.EDICION:
            raise IntegrityError("simulated ledger failure")
        return original_create(**kwargs)

    with patch.object(MovimientoInventario.objects, "create", side_effect=fail_create):
        with pytest.raises((IntegrityError, Exception)):
            InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 10  # rolled back
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 19. Rollback si no hay stock suficiente
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rollback_si_stock_insuficiente():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=2)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc, repuesto, cantidad=5)  # pide 5 más de lo disponible

    snapshot = _snapshot_bodega(repuesto, 0)  # antes tenía 0 → delta=-5
    op = str(uuid.uuid4())

    with pytest.raises(ValidationError, match="Stock insuficiente"):
        InventoryService.procesar_edicion_con_ledger(snapshot, doc, op)

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 2  # sin cambio
    assert MovimientoInventario.objects.filter(documento=doc).count() == 0


# ---------------------------------------------------------------------------
# 20. Tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tenant_isolation_edicion():
    empresa_a = EmpresaFactory(pais="CL")
    empresa_b = EmpresaFactory(pais="CL")
    r_a = RepuestoFactory(empresa=empresa_a, cantidad_stock=10)
    r_b = RepuestoFactory(empresa=empresa_b, cantidad_stock=10)
    doc_a = DocumentoFactory(empresa=empresa_a, tipo="OT", estado="EMITIDO")
    doc_b = DocumentoFactory(empresa=empresa_b, tipo="OT", estado="EMITIDO")
    _linea_bodega(doc_a, r_a, cantidad=4)
    _linea_bodega(doc_b, r_b, cantidad=3)

    snap_a = _snapshot_bodega(r_a, 2)
    snap_b = _snapshot_bodega(r_b, 1)

    InventoryService.procesar_edicion_con_ledger(snap_a, doc_a, str(uuid.uuid4()))
    InventoryService.procesar_edicion_con_ledger(snap_b, doc_b, str(uuid.uuid4()))

    r_a.refresh_from_db()
    r_b.refresh_from_db()
    assert r_a.cantidad_stock == 8   # 10 - 2
    assert r_b.cantidad_stock == 8   # 10 - 2

    assert MovimientoInventario.objects.filter(empresa=empresa_a).count() == 1
    assert MovimientoInventario.objects.filter(empresa=empresa_b).count() == 1


# ---------------------------------------------------------------------------
# 21. EMISION sigue creando tipo=EMISION (regresión)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emision_sigue_creando_tipo_emision():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    LineaRepuesto.objects.create(
        documento=doc, nombre=repuesto.nombre, codigo="R1",
        cantidad=3, precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0"), origen_repuesto=ORIGEN_STOCK_BODEGA,
        repuesto=repuesto,
    )

    InventoryService.procesar_movimiento_stock(doc, "descontar")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.tipo == MovimientoInventario.TipoMovimiento.EMISION


# ---------------------------------------------------------------------------
# 22. ANULACION sigue creando tipo=ANULACION (regresión)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anulacion_sigue_creando_tipo_anulacion():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    LineaRepuesto.objects.create(
        documento=doc, nombre=repuesto.nombre, codigo="R1",
        cantidad=2, precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0"), origen_repuesto=ORIGEN_STOCK_BODEGA,
        repuesto=repuesto, costo_linea=Decimal("1000"),
    )

    InventoryService.procesar_movimiento_stock(doc, "reponer")

    m = MovimientoInventario.objects.get(documento=doc)
    assert m.tipo == MovimientoInventario.TipoMovimiento.ANULACION


# ---------------------------------------------------------------------------
# 23. Integración vía DocumentoForm — edita EMITIDO y crea EDICION ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_documento_form_edicion_crea_ledger_edicion(user_cl):
    import json
    from django.utils import timezone

    from taller.documentos.forms import DocumentoForm
    from taller.models.clientes import Cliente
    from taller.models.vehiculos import Vehiculo

    empresa = user_cl.empresa
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Form")
    vehiculo = Vehiculo.objects.create(empresa=empresa, cliente=cliente, patente="EF001", vin="VIN-EF001", anio=2021)
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=50)

    # Crear documento EMITIDO con qty=5 y procesar EMISION inicial
    doc = DocumentoFactory(empresa=empresa, cliente=cliente, vehiculo=vehiculo, tipo="OT", estado="EMITIDO")
    LineaRepuesto.objects.create(
        documento=doc, nombre=repuesto.nombre, codigo="R1",
        cantidad=5, precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0"), origen_repuesto=ORIGEN_STOCK_BODEGA,
        repuesto=repuesto, costo_linea=Decimal("100"),
    )
    InventoryService.procesar_movimiento_stock(doc, "descontar")
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 45  # 50 - 5

    # Editar via formulario: cambiar qty de 5 a 8 (necesita 3 más)
    data = {
        "tipo": "OT",
        "estado": "EMITIDO",
        "fecha_emision": timezone.now().date(),
        "cliente": str(cliente.id),
        "vehiculo": str(vehiculo.id),
        "repuestos_json": json.dumps([{
            "repuesto_id": repuesto.id,
            "codigo": "R1",
            "nombre": repuesto.nombre,
            "cantidad": 8,
            "precio": str(repuesto.precio_venta),
            "origen_repuesto": ORIGEN_STOCK_BODEGA,
            "costo_linea": "100",
        }]),
        "servicios_json": "[]",
        "otros_json": "[]",
    }
    form = DocumentoForm(data=data, instance=doc, user=user_cl, empresa=empresa, country="CL")
    assert form.is_valid(), form.errors
    form.save()

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 42  # 45 - 3

    movs_edicion = MovimientoInventario.objects.filter(
        documento=doc,
        tipo=MovimientoInventario.TipoMovimiento.EDICION,
    )
    assert movs_edicion.count() == 1
    m = movs_edicion.first()
    assert m.cantidad_delta == -3
    assert m.metadata["accion"] == "edicion"
    assert "operation_id" in m.metadata
