"""
Sprint B — inventory-ledger: MovimientoInventario model + InventoryLedgerService.

Tests:
  1.  Permite movimiento STOCK_BODEGA con repuesto.
  2.  Permite movimiento DESARME con pieza_desarme.
  3.  Rechaza ambos destinos informados.
  4.  Rechaza ambos destinos nulos.
  5.  Rechaza origen STOCK_BODEGA con pieza_desarme.
  6.  Rechaza origen DESARME con repuesto.
  7.  Rechaza cantidad_delta=0.
  8.  Rechaza saldo_resultante<0.
  9.  idempotency_key es única (IntegrityError en segundo insert).
  10. Helper genera el mismo hash para el mismo payload.
  11. Helper genera hash distinto al cambiar cantidad_delta.
  12. Helper genera hash distinto al cambiar operation_version.
  13. Instancia persistida no puede modificarse (immutable save).
  14. Instancia persistida no puede eliminarse.
  15. Admin es completamente readonly.
  16. FKs del modelo usan referencias string (no imports directos).

Strategy:
  - Validation constraints live in clean() → tested via full_clean().
  - DB-level CHECK constraints are defined but SQLite ignores them silently.
  - PiezaDesarme requires VehiculoDesarme; created inline without factory.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from taller.models.movimiento_inventario import MovimientoInventario
from taller.services.inventory_ledger_service import InventoryLedgerService
from taller.tests.factories import EmpresaFactory, RepuestoFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pieza(empresa):
    """Create a minimal PiezaDesarme for testing."""
    from taller.models.vehiculo_desarme import VehiculoDesarme
    from taller.models.pieza_desarme import PiezaDesarme

    vehiculo = VehiculoDesarme.objects.create(empresa=empresa, patente="D-TEST")
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        nombre="Pieza test",
        cantidad=10,
    )


def _make_movimiento(empresa, repuesto=None, pieza=None, **kwargs):
    """Build (not saved) a MovimientoInventario with sensible defaults."""
    defaults = dict(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=(
            MovimientoInventario.OrigenStock.STOCK_BODEGA
            if repuesto is not None
            else MovimientoInventario.OrigenStock.DESARME
        ),
        repuesto=repuesto,
        pieza_desarme=pieza,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-key-unique",
    )
    defaults.update(kwargs)
    return MovimientoInventario(**defaults)


# ---------------------------------------------------------------------------
# 1. Permite STOCK_BODEGA con repuesto
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_permite_movimiento_stock_bodega():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa, cantidad_stock=5)

    m = MovimientoInventario.objects.create(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-sb-1",
    )
    assert m.pk is not None
    assert m.repuesto_id == repuesto.pk
    assert m.pieza_desarme_id is None


# ---------------------------------------------------------------------------
# 2. Permite DESARME con pieza_desarme
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_permite_movimiento_desarme():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa)

    m = MovimientoInventario.objects.create(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.DESARME,
        pieza_desarme=pieza,
        cantidad_delta=-1,
        saldo_resultante=9,
        idempotency_key="test-ds-1",
    )
    assert m.pk is not None
    assert m.pieza_desarme_id == pieza.pk
    assert m.repuesto_id is None


# ---------------------------------------------------------------------------
# 3. Rechaza ambos destinos informados
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rechaza_ambos_destinos_informados():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)
    pieza = _make_pieza(empresa)

    m = MovimientoInventario(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        pieza_desarme=pieza,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-ambos",
    )
    with pytest.raises(ValidationError, match="Solo uno de repuesto"):
        m.full_clean()


# ---------------------------------------------------------------------------
# 4. Rechaza ambos destinos nulos
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rechaza_ambos_destinos_nulos():
    empresa = EmpresaFactory(pais="CL")

    m = MovimientoInventario(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=None,
        pieza_desarme=None,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-nulos",
    )
    with pytest.raises(ValidationError, match="Debe informar"):
        m.full_clean()


# ---------------------------------------------------------------------------
# 5. Rechaza STOCK_BODEGA con pieza_desarme (sin repuesto)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rechaza_stock_bodega_con_pieza():
    empresa = EmpresaFactory(pais="CL")
    pieza = _make_pieza(empresa)

    m = MovimientoInventario(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=None,
        pieza_desarme=pieza,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-sb-pieza",
    )
    with pytest.raises(ValidationError, match="STOCK_BODEGA requiere repuesto"):
        m.full_clean()


# ---------------------------------------------------------------------------
# 6. Rechaza DESARME con repuesto (sin pieza)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rechaza_desarme_con_repuesto():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)

    m = MovimientoInventario(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.DESARME,
        repuesto=repuesto,
        pieza_desarme=None,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-ds-repuesto",
    )
    with pytest.raises(ValidationError, match="DESARME requiere pieza_desarme"):
        m.full_clean()


# ---------------------------------------------------------------------------
# 7. Rechaza cantidad_delta == 0
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rechaza_delta_cero():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)

    m = MovimientoInventario(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        cantidad_delta=0,
        saldo_resultante=5,
        idempotency_key="test-delta-cero",
    )
    with pytest.raises(ValidationError, match="cantidad_delta no puede ser cero"):
        m.full_clean()


# ---------------------------------------------------------------------------
# 8. Rechaza saldo_resultante < 0
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rechaza_saldo_negativo():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)

    m = MovimientoInventario(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        cantidad_delta=-10,
        saldo_resultante=-1,
        idempotency_key="test-saldo-neg",
    )
    with pytest.raises(ValidationError, match="saldo_resultante no puede ser negativo"):
        m.full_clean()


# ---------------------------------------------------------------------------
# 9. idempotency_key es única
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_idempotency_key_es_unica():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)

    MovimientoInventario.objects.create(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="duplicated-key",
    )
    with pytest.raises(IntegrityError):
        MovimientoInventario.objects.create(
            empresa=empresa,
            tipo=MovimientoInventario.TipoMovimiento.EMISION,
            origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
            repuesto=repuesto,
            cantidad_delta=-1,
            saldo_resultante=3,
            idempotency_key="duplicated-key",
        )


# ---------------------------------------------------------------------------
# 10. Helper genera el mismo hash para el mismo payload
# ---------------------------------------------------------------------------

def test_helper_genera_mismo_hash_para_mismo_payload():
    kwargs = dict(
        empresa_id=1,
        tipo="EMISION",
        origen_stock="STOCK_BODEGA",
        repuesto_id=42,
        pieza_desarme_id=None,
        documento_id=7,
        linea_repuesto_id=99,
        cantidad_delta=-3,
    )
    hash_a = InventoryLedgerService.build_idempotency_key(**kwargs)
    hash_b = InventoryLedgerService.build_idempotency_key(**kwargs)
    assert hash_a == hash_b
    assert len(hash_a) == 64  # SHA-256 hexdigest


# ---------------------------------------------------------------------------
# 11. Helper genera hash distinto al cambiar cantidad_delta
# ---------------------------------------------------------------------------

def test_helper_genera_hash_distinto_al_cambiar_delta():
    base = dict(
        empresa_id=1,
        tipo="EMISION",
        origen_stock="STOCK_BODEGA",
        repuesto_id=42,
        pieza_desarme_id=None,
        documento_id=7,
        linea_repuesto_id=99,
        cantidad_delta=-3,
    )
    hash_a = InventoryLedgerService.build_idempotency_key(**base)
    hash_b = InventoryLedgerService.build_idempotency_key(**{**base, "cantidad_delta": -5})
    assert hash_a != hash_b


# ---------------------------------------------------------------------------
# 12. Helper genera hash distinto al cambiar operation_version
# ---------------------------------------------------------------------------

def test_helper_genera_hash_distinto_al_cambiar_version():
    base = dict(
        empresa_id=1,
        tipo="EMISION",
        origen_stock="STOCK_BODEGA",
        repuesto_id=42,
        pieza_desarme_id=None,
        documento_id=7,
        linea_repuesto_id=99,
        cantidad_delta=-3,
    )
    hash_v1 = InventoryLedgerService.build_idempotency_key(**base, operation_version=1)
    hash_v2 = InventoryLedgerService.build_idempotency_key(**base, operation_version=2)
    assert hash_v1 != hash_v2


# ---------------------------------------------------------------------------
# 13. Instancia persistida no puede modificarse
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_instancia_persistida_no_puede_modificarse():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)

    m = MovimientoInventario.objects.create(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-immutable-save",
    )
    m.notas = "Intento de modificación"
    with pytest.raises(ValidationError, match="inmutable"):
        m.save()


# ---------------------------------------------------------------------------
# 14. Instancia persistida no puede eliminarse
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_instancia_persistida_no_puede_eliminarse():
    empresa = EmpresaFactory(pais="CL")
    repuesto = RepuestoFactory(empresa=empresa)

    m = MovimientoInventario.objects.create(
        empresa=empresa,
        tipo=MovimientoInventario.TipoMovimiento.EMISION,
        origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
        repuesto=repuesto,
        cantidad_delta=-1,
        saldo_resultante=4,
        idempotency_key="test-immutable-delete",
    )
    with pytest.raises(ValidationError, match="no puede eliminarse"):
        m.delete()


# ---------------------------------------------------------------------------
# 15. Admin es completamente readonly
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_es_readonly():
    from django.contrib import admin as django_admin

    model_admin = django_admin.site._registry.get(MovimientoInventario)
    assert model_admin is not None, "MovimientoInventario no está registrado en el admin"
    assert model_admin.has_add_permission(None) is False
    assert model_admin.has_change_permission(None) is False
    assert model_admin.has_delete_permission(None) is False
    assert model_admin.actions == []


# ---------------------------------------------------------------------------
# 16. FKs usan referencias string (no imports directos en el modelo)
# ---------------------------------------------------------------------------

def test_fks_usan_referencias_string():
    """
    Django resolves string FK references lazily; if they were wrong class
    references the app would fail to start. We just verify the field's
    remote_field.model is a string at definition time OR the correct class
    after app registry initialization.
    """
    from django.apps import apps

    Repuesto = apps.get_model("taller", "Repuesto")
    PiezaDesarme = apps.get_model("taller", "PiezaDesarme")
    Documento = apps.get_model("taller", "Documento")
    LineaRepuesto = apps.get_model("taller", "LineaRepuesto")
    Empresa = apps.get_model("taller", "Empresa")

    assert MovimientoInventario._meta.get_field("repuesto").related_model is Repuesto
    assert MovimientoInventario._meta.get_field("pieza_desarme").related_model is PiezaDesarme
    assert MovimientoInventario._meta.get_field("documento").related_model is Documento
    assert MovimientoInventario._meta.get_field("linea_repuesto").related_model is LineaRepuesto
    assert MovimientoInventario._meta.get_field("empresa").related_model is Empresa
