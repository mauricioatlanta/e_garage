from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_STOCK_BODEGA
from taller.models.empresa import Empresa
from taller.models.repuesto import Repuesto
from taller.services.inventory_intelligence import InventoryIntelligenceService
from taller.views.reabastecimiento import ReabastecimientoPanelView


@pytest.mark.django_db
def test_inventory_intelligence_calcula_cobertura_y_sugerencia():
    from taller.tests.factories import EmpresaFactory
    empresa = EmpresaFactory(nombre_taller="EG Stock", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Stock")
    repuesto = Repuesto.objects.create(
        empresa=empresa,
        part_number="FLT-100",
        nombre="Filtro de aceite",
        cantidad_stock=4,
        stock_minimo=6,
        precio_venta=Decimal("15990.00"),
    )
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        tipo="FAC",
        estado="EMITIDO",
    )
    LineaRepuesto.objects.create(
        documento=documento,
        repuesto=repuesto,
        codigo="FLT-100",
        nombre="Filtro de aceite",
        cantidad=15,
        precio_unitario=Decimal("15990.00"),
        origen_repuesto=ORIGEN_STOCK_BODEGA,
    )

    panel = InventoryIntelligenceService.build_panel(
        empresa=empresa,
        queryset=Repuesto.objects.filter(pk=repuesto.pk),
        lookback_days=30,
        target_coverage_days=30,
    )

    row = panel["rows"][0]
    assert row["consumo_diario"] == Decimal("0.50")
    assert row["dias_cobertura"] == Decimal("8.0")
    assert row["sugerencia_compra"] == 11
    assert row["status"] == "warning"
    assert row["alert_state"] == "low"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("stock", "minimum", "expected"),
    [
        (6, 5, None),
        (5, 5, "low"),
        (1, 5, "low"),
        (0, 5, "out"),
        (0, 0, "out"),
        (0, None, None),
    ],
)
def test_restock_alert_states_distinguish_disabled_and_zero(stock, minimum, expected):
    from taller.tests.factories import EmpresaFactory

    empresa = EmpresaFactory(nombre_taller=f"Alert {stock} {minimum}", pais="CL")
    repuesto = Repuesto.objects.create(
        empresa=empresa,
        part_number=f"A-{stock}-{minimum}",
        nombre="Filtro",
        cantidad_stock=stock,
        stock_minimo=minimum,
    )
    snapshot = InventoryIntelligenceService.build_repuesto_snapshot(repuesto)
    assert snapshot["alert_state"] == expected
    assert snapshot["alert_enabled"] is (minimum is not None)


@pytest.mark.django_db
def test_document_alerts_are_company_scoped_and_ignore_external_or_desarme():
    from taller.tests.factories import EmpresaFactory
    from taller.models.lineas_documento import ORIGEN_EXTERNO

    empresa = EmpresaFactory(nombre_taller="Empresa alerta", pais="CL")
    otra = EmpresaFactory(nombre_taller="Otra empresa", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente")
    doc = Documento.objects.create(empresa=empresa, cliente=cliente, tipo="OT", estado="EMITIDO")
    low = Repuesto.objects.create(
        empresa=empresa, part_number="LOW-1", nombre="Filtro", cantidad_stock=2, stock_minimo=3
    )
    foreign = Repuesto.objects.create(
        empresa=otra, part_number="FOREIGN-1", nombre="Ajeno", cantidad_stock=0, stock_minimo=4
    )
    LineaRepuesto.objects.create(
        documento=doc, repuesto=low, codigo="LOW-1", nombre="Filtro", cantidad=1,
        precio_unitario=1, origen_repuesto=ORIGEN_STOCK_BODEGA,
    )
    LineaRepuesto.objects.create(
        documento=doc, codigo="EXT-1", nombre="Compra específica", cantidad=1,
        precio_unitario=1, origen_repuesto=ORIGEN_EXTERNO,
    )

    alerts = InventoryIntelligenceService.get_document_restock_alerts(doc)
    assert [row["repuesto"].pk for row in alerts] == [low.pk]
    assert foreign.pk not in [row["repuesto"].pk for row in alerts]


@pytest.mark.django_db
def test_restock_panel_uses_active_request_company_in_qa_context():
    from taller.tests.factories import EmpresaFactory

    owner_company = EmpresaFactory(nombre_taller="Owner", pais="CL")
    active_company = EmpresaFactory(nombre_taller="QA activa", pais="CL")
    own_part = Repuesto.objects.create(
        empresa=owner_company, part_number="OWN", nombre="Propio", cantidad_stock=1
    )
    active_part = Repuesto.objects.create(
        empresa=active_company, part_number="ACTIVE", nombre="Activo", cantidad_stock=1
    )
    request = RequestFactory().get("/cl/es/repuestos/reabastecimiento/")
    request.user = owner_company.user
    request.empresa = active_company
    view = ReabastecimientoPanelView()
    view.request = request

    ids = list(view.get_queryset().values_list("id", flat=True))
    assert ids == [active_part.id]
    assert own_part.id not in ids
