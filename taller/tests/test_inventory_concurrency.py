"""
Sprint A — inventory-ledger: concurrency guards for STOCK_BODEGA emission.

Tests:
  1.  select_for_update called for STOCK_BODEGA repuestos inside emitir_documento
  2.  select_for_update NOT called when documento has no STOCK_BODEGA lines
  3.  Signal no-ops when estado unchanged (double-save guard)
  4.  Double procesar_movimiento_stock("descontar") on same doc descounts twice
      — confirms stock guard must live at the view/lock level, not service
  5.  Emitting a PRES document never touches stock (TIPOS_SIN_STOCK guard)
  6.  validar_stock_disponible returns error when stock == cantidad required
      (boundary: stock == 0 after decrement)
  7.  Concurrent decrements via F() are additive — two sequential calls both apply
  8.  EXTERNO lines never move stock even when emitting

Strategy:
  - SQLite ignores select_for_update() silently, so concurrency lock tests use
    unittest.mock.patch to assert the queryset method is called with the right args.
  - Actual stock arithmetic tests call InventoryService directly (no thread forking).
  - No new model (MovimientoInventario) introduced in this sprint.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_STOCK_BODEGA,
    ORIGEN_EXTERNO,
)
from taller.models.repuesto import Repuesto
from taller.services.inventory_service import InventoryService
from taller.tests.factories import (
    DocumentoFactory,
    EmpresaFactory,
    RepuestoFactory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request_with_messages(method, path, user):
    factory = RequestFactory()
    request = getattr(factory, method)(path)
    request.user = user
    setattr(request, "session", "session")
    setattr(request, "_messages", FallbackStorage(request))
    return request


def _make_linea(doc, repuesto, *, cantidad=1, origen=ORIGEN_STOCK_BODEGA):
    return LineaRepuesto.objects.create(
        documento=doc,
        nombre=repuesto.nombre,
        codigo=repuesto.part_number or "TEST",
        cantidad=cantidad,
        precio_unitario=repuesto.precio_venta,
        descuento=Decimal("0.00"),
        origen_repuesto=origen,
        repuesto=repuesto if origen == ORIGEN_STOCK_BODEGA else None,
    )


# ---------------------------------------------------------------------------
# 1. select_for_update is requested for STOCK_BODEGA lines in emitir_documento
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emitir_documento_adquiere_lock_en_repuestos_bodega():
    """
    emitir_documento() must call select_for_update() on STOCK_BODEGA Repuesto
    rows inside the atomic block — before validation and save.
    """
    from taller.documentos.views_inventory import emitir_documento

    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea(doc, repuesto, cantidad=2)

    request = _request_with_messages("post", f"/cl/documentos/emitir/{doc.pk}/", empresa.user)

    sfu_qs = MagicMock()
    sfu_qs.filter.return_value = []

    with patch.object(Repuesto.objects, "select_for_update", return_value=sfu_qs) as mock_sfu:
        with patch("taller.documentos.views_inventory.InventoryService.validar_stock_disponible", return_value=[]):
            with patch("taller.models.documento.Documento.save"):
                emitir_documento(request, doc.pk)

    mock_sfu.assert_called_once()
    sfu_qs.filter.assert_called_once()
    call_kwargs = sfu_qs.filter.call_args.kwargs
    assert "id__in" in call_kwargs
    assert repuesto.pk in call_kwargs["id__in"]


# ---------------------------------------------------------------------------
# 2. select_for_update NOT called when no STOCK_BODEGA lines exist
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_emitir_documento_sin_lineas_bodega_no_adquiere_lock():
    """
    No STOCK_BODEGA lines → the select_for_update() branch is skipped entirely.
    """
    from taller.documentos.views_inventory import emitir_documento

    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
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

    request = _request_with_messages("post", f"/cl/documentos/emitir/{doc.pk}/", empresa.user)

    with patch.object(Repuesto.objects, "select_for_update") as mock_sfu:
        with patch("taller.documentos.views_inventory.InventoryService.validar_stock_disponible", return_value=[]):
            with patch("taller.models.documento.Documento.save"):
                emitir_documento(request, doc.pk)

    mock_sfu.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Signal no-ops when estado unchanged (double-save guard)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_signal_noop_cuando_estado_no_cambia():
    """
    pre_save signal returns without calling InventoryService when estado didn't change.
    """
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea(doc, repuesto, cantidad=1)

    stock_before = Repuesto.objects.get(pk=repuesto.pk).cantidad_stock

    # Save same estado — signal must be a no-op
    doc.estado = "BORRADOR"
    doc.save()

    stock_after = Repuesto.objects.get(pk=repuesto.pk).cantidad_stock
    assert stock_after == stock_before


# ---------------------------------------------------------------------------
# 4. Double-descontar subtracts twice — confirms lock is needed at view level
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_double_descontar_resta_dos_veces():
    """
    Calling procesar_movimiento_stock("descontar") twice is NOT idempotent.
    This confirms that the protection must live at the lock layer (view), not
    the service layer.
    """
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=10)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    _make_linea(doc, repuesto, cantidad=3)

    InventoryService.procesar_movimiento_stock(doc, "descontar")
    InventoryService.procesar_movimiento_stock(doc, "descontar")

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 4  # 10 - 3 - 3


# ---------------------------------------------------------------------------
# 5. PRES documents never touch stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_pres_no_mueve_stock():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)
    doc = DocumentoFactory(empresa=empresa, tipo="PRES", estado="EMITIDO")
    _make_linea(doc, repuesto, cantidad=3)

    resultado = InventoryService.procesar_movimiento_stock(doc, "descontar")

    assert resultado["procesado"] is False
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 5


# ---------------------------------------------------------------------------
# 6. validar_stock_disponible: stock == cantidad requerida is OK (boundary)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_validar_stock_exacto_no_genera_error():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=3)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea(doc, repuesto, cantidad=3)

    errores = InventoryService.validar_stock_disponible(doc)
    assert errores == []


@pytest.mark.django_db
def test_validar_stock_insuficiente_genera_error():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=2)
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="BORRADOR")
    _make_linea(doc, repuesto, cantidad=3)

    errores = InventoryService.validar_stock_disponible(doc)
    assert len(errores) == 1
    assert repuesto.nombre in errores[0]


# ---------------------------------------------------------------------------
# 7. F()-based decrements are additive (not last-write-wins)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_f_expression_decrements_are_additive():
    """
    Two sequential F()-based updates both apply correctly — confirms F() avoids
    read-modify-write race at the SQL level.
    """
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=20)
    doc_a = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    doc_b = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    _make_linea(doc_a, repuesto, cantidad=5)
    _make_linea(doc_b, repuesto, cantidad=7)

    InventoryService.procesar_movimiento_stock(doc_a, "descontar")
    InventoryService.procesar_movimiento_stock(doc_b, "descontar")

    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 8  # 20 - 5 - 7


# ---------------------------------------------------------------------------
# 8. EXTERNO lines never move stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_externo_no_mueve_stock():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="FAC", estado="EMITIDO")
    LineaRepuesto.objects.create(
        documento=doc,
        nombre="Mano de obra externa",
        codigo="EXT-1",
        cantidad=1,
        precio_unitario=Decimal("10000"),
        descuento=Decimal("0.00"),
        origen_repuesto=ORIGEN_EXTERNO,
        repuesto=None,
    )

    resultado = InventoryService.procesar_movimiento_stock(doc, "descontar")
    assert resultado["procesado"] is False
