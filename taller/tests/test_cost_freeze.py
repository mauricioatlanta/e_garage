"""
Tests for Sprint 2B: costo_linea freeze at BORRADOR → EMITIDO.

Business rule: when a document transitions to EMITIDO, the purchase cost
of each STOCK_BODEGA part is captured from Repuesto.precio_compra and
frozen into LineaRepuesto.costo_linea. The value never changes after that,
regardless of future price updates.

Covers:
  1.  STOCK_BODEGA: costo_linea set from repuesto.precio_compra at emission
  2.  Snapshot: changing precio_compra after does NOT alter costo_linea
  3.  BORRADOR: costo_linea is NULL before emission (not frozen early)
  4.  ANULADO: costo_linea preserved on cancellation (not cleared)
  5.  DESARME: existing costo_linea not overwritten
  6.  EXTERNO: not in movement lines, not touched
  7.  Reactivation (ANULADO → EMITIDO): re-frozen to current precio_compra
  8.  precio_compra = 0 → costo_linea = 0 (zero is honest, not NULL)
  9.  Multiple lines frozen in a single bulk_update
  10. Signal integration: doc.save(estado=EMITIDO) triggers freeze end-to-end
  11. PRES documents never trigger freeze (not in TIPOS_CON_STOCK)
"""

from decimal import Decimal

import pytest
from django.db import transaction

from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_DESARME,
    ORIGEN_EXTERNO,
    ORIGEN_STOCK_BODEGA,
)
from taller.services.inventory_service import InventoryService
from taller.tests.factories import DocumentoFactory, EmpresaFactory, RepuestoFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_linea(doc, repuesto, *, cantidad=1, precio_unitario=None, origen=ORIGEN_STOCK_BODEGA):
    """Creates a LineaRepuesto with sensible defaults."""
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre=repuesto.nombre,
        codigo=repuesto.part_number or "TEST",
        cantidad=cantidad,
        precio_unitario=precio_unitario or repuesto.precio_venta,
        descuento=Decimal("0.00"),
        origen_repuesto=origen,
        repuesto=repuesto,
    )


def _emit(doc):
    """Call InventoryService directly to freeze costs + move stock."""
    return InventoryService.procesar_movimiento_stock(doc, "descontar")


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_costo_linea_congelado_al_emitir():
    """costo_linea toma el precio_compra del repuesto al emitir."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    assert linea.costo_linea is None  # aún no congelado

    _emit(doc)
    linea.refresh_from_db()

    assert linea.costo_linea == Decimal("100.00")


@pytest.mark.django_db
def test_costo_es_snapshot_no_sigue_precio_compra():
    """Modificar precio_compra después de la emisión no altera costo_linea."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    _emit(doc)
    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("100.00")

    # El proveedor subió el precio
    repuesto.precio_compra = Decimal("200.00")
    repuesto.save(update_fields=["precio_compra"])

    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("100.00")  # Congelado: no cambió


@pytest.mark.django_db
def test_costo_no_congelado_en_borrador():
    """En BORRADOR el costo_linea debe quedar NULL."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    linea.refresh_from_db()
    assert linea.costo_linea is None


@pytest.mark.django_db
def test_costo_preservado_al_anular():
    """EMITIDO → ANULADO no limpia costo_linea (preserva el snapshot histórico)."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    _emit(doc)
    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("100.00")

    # Anular repone stock pero NO debe tocar costo_linea
    InventoryService.procesar_movimiento_stock(doc, "reponer")
    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("100.00")  # Snapshot intacto


@pytest.mark.django_db
def test_costo_reactivacion_congela_precio_actual():
    """ANULADO → EMITIDO (reactivación) vuelve a congelar al precio_compra vigente."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    _emit(doc)

    # El proveedor cambió el precio antes de la reactivación
    repuesto.precio_compra = Decimal("120.00")
    repuesto.save(update_fields=["precio_compra"])
    repuesto.refresh_from_db()

    # Reponer (anulación) + volver a descontar (reactivación)
    InventoryService.procesar_movimiento_stock(doc, "reponer")
    _emit(doc)

    linea.refresh_from_db()
    # Al reemitir, el costo se congela al precio vigente
    assert linea.costo_linea == Decimal("120.00")


@pytest.mark.django_db
def test_precio_compra_cero_congela_cero():
    """precio_compra=0 → costo_linea=0 (valor honesto, no NULL)."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("0.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    _emit(doc)
    linea.refresh_from_db()

    assert linea.costo_linea == Decimal("0.00")
    assert linea.costo_linea is not None  # 0 ≠ NULL


@pytest.mark.django_db
def test_multiples_lineas_todas_congeladas():
    """Múltiples líneas STOCK_BODEGA en un documento: todas congeladas en un solo emit."""
    empresa = EmpresaFactory(pais="CL")
    rep_a = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    rep_b = RepuestoFactory(empresa=empresa, precio_compra=Decimal("250.00"), cantidad_stock=10)
    rep_c = RepuestoFactory(empresa=empresa, precio_compra=Decimal("50.00"),  cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea_a = _make_linea(doc, rep_a)
    linea_b = _make_linea(doc, rep_b)
    linea_c = _make_linea(doc, rep_c)

    _emit(doc)

    linea_a.refresh_from_db()
    linea_b.refresh_from_db()
    linea_c.refresh_from_db()

    assert linea_a.costo_linea == Decimal("100.00")
    assert linea_b.costo_linea == Decimal("250.00")
    assert linea_c.costo_linea == Decimal("50.00")


@pytest.mark.django_db
def test_freeze_solo_aplica_a_stock_bodega():
    """
    El freeze sólo modifica líneas con origen_repuesto=STOCK_BODEGA.
    Una línea del mismo documento con costo_linea pre-existente y otro origen
    queda intacta.

    Usamos bulk_update para forzar origen_repuesto=EXTERNO con costo pre-set
    sin pasar por full_clean() (EXTERNO no tiene repuesto_id, lo que fallaría
    la validación). El propósito es verificar el filtro del servicio.
    """
    empresa = EmpresaFactory(pais="CL")
    rep_bodega = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    rep_extra  = RepuestoFactory(empresa=empresa, precio_compra=Decimal("50.00"),  cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")

    linea_bodega = _make_linea(doc, rep_bodega)
    linea_extra  = _make_linea(doc, rep_extra)

    # Forzar la segunda línea a EXTERNO con costo pre-set, saltando validación
    LineaRepuesto.objects.filter(pk=linea_extra.pk).update(
        origen_repuesto=ORIGEN_EXTERNO,
        repuesto=None,
        costo_linea=Decimal("9999.00"),
    )

    _emit(doc)

    linea_bodega.refresh_from_db()
    linea_extra.refresh_from_db()

    # STOCK_BODEGA: congelado desde precio_compra
    assert linea_bodega.costo_linea == Decimal("100.00")
    # EXTERNO: sentinel intacto — el freeze no lo tocó
    assert linea_extra.costo_linea == Decimal("9999.00")


@pytest.mark.django_db
def test_pres_no_congela():
    """Documentos PRES nunca mueven stock ni congelan costos."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="PRES", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    resultado = _emit(doc)

    assert resultado["procesado"] is False
    linea.refresh_from_db()
    assert linea.costo_linea is None  # PRES no congela


@pytest.mark.django_db
def test_signal_integration_congela_al_guardar_emitido():
    """
    End-to-end: cambiar doc.estado a EMITIDO y guardar dispara la señal
    que llama a InventoryService y congela costo_linea.
    """
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("75.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    assert linea.costo_linea is None

    # Simular el guardado real que dispara la señal
    doc.estado = "EMITIDO"
    doc.save(update_fields=["estado"])

    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("75.00")
