"""
Tests for Sprint 2B: costo_linea freeze at BORRADOR → EMITIDO.

Business rule: when a document transitions to EMITIDO, the purchase cost
of each STOCK_BODEGA part is captured from Repuesto.precio_compra and
frozen into LineaRepuesto.costo_linea. The value never changes after that,
regardless of future price updates.

Covers:
  1.  STOCK_BODEGA: costo_linea set from repuesto.precio_compra at emission
  2.  Snapshot: changing precio_compra after does NOT alter costo_linea
  3.  No overwrite: existing costo_linea is NOT overwritten on re-emit
  4.  BORRADOR: costo_linea is NULL before emission (not frozen early)
  5.  ANULADO: costo_linea preserved on cancellation (not cleared)
  6.  Reactivation (ANULADO → EMITIDO): original snapshot preserved
  7.  precio_compra = 0 → costo_linea = 0 (zero is honest, not NULL)
  8.  Multiple lines frozen in a single bulk_update
  9.  Origin filter: only STOCK_BODEGA lines are frozen
  10. PRES documents never trigger freeze (not in TIPOS_CON_STOCK)
  11. Signal integration: doc.save(estado=EMITIDO) triggers freeze end-to-end
  12. Rollback atómico: bulk_update failure rolls back both stock and costo_linea
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import transaction
from django.db.models import QuerySet

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
def test_no_sobrescribe_snapshot_existente():
    """Un costo_linea ya congelado NO se sobreescribe en re-emisiones."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    _emit(doc)
    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("100.00")

    # El proveedor subió el precio
    repuesto.precio_compra = Decimal("999.00")
    repuesto.save(update_fields=["precio_compra"])

    # Segunda llamada "descontar" (simula doble-save o bug de señal)
    _emit(doc)
    linea.refresh_from_db()

    # El snapshot original no fue sobreescrito
    assert linea.costo_linea == Decimal("100.00")


@pytest.mark.django_db
def test_snapshot_preservado_en_reactivacion():
    """ANULADO → EMITIDO (reactivación) preserva el costo_linea original."""
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    linea = _make_linea(doc, repuesto)

    _emit(doc)
    linea.refresh_from_db()
    assert linea.costo_linea == Decimal("100.00")

    # El proveedor cambió el precio antes de la reactivación
    repuesto.precio_compra = Decimal("200.00")
    repuesto.save(update_fields=["precio_compra"])

    # Reponer (anulación) + volver a descontar (reactivación)
    InventoryService.procesar_movimiento_stock(doc, "reponer")
    _emit(doc)

    linea.refresh_from_db()
    # El snapshot original debe quedar intacto — no re-congela al nuevo precio
    assert linea.costo_linea == Decimal("100.00")


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


@pytest.mark.django_db
def test_rollback_atomico_si_falla_bulk_update():
    """
    Si bulk_update falla, la transacción completa se revierte:
    el stock NO se descuenta y costo_linea permanece NULL.
    """
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, precio_compra=Decimal("100.00"), cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    _make_linea(doc, repuesto)

    stock_antes = repuesto.cantidad_stock

    with patch.object(
        QuerySet, "bulk_update", side_effect=Exception("DB failure simulado")
    ):
        with pytest.raises(Exception, match="DB failure simulado"):
            _emit(doc)

    repuesto.refresh_from_db()
    # Toda la transacción se revirtió: stock intacto
    assert repuesto.cantidad_stock == stock_antes

    # costo_linea también intacto (la línea nunca fue actualizada)
    linea = doc.lineas_repuesto.filter(origen_repuesto=ORIGEN_STOCK_BODEGA).first()
    assert linea.costo_linea is None
