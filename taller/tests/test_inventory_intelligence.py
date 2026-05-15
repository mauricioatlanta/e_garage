from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_STOCK_BODEGA
from taller.models.empresa import Empresa
from taller.models.repuesto import Repuesto
from taller.services.inventory_intelligence import InventoryIntelligenceService


@pytest.mark.django_db
def test_inventory_intelligence_calcula_cobertura_y_sugerencia():
    user = User.objects.create_user(username="stock-panel", password="pass")
    empresa = Empresa.objects.create(user=user, nombre_taller="EG Stock", pais="CL")
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
