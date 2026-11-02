import json
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from taller.desarme.forms import VehiculoDesarmeForm
from taller.models.compatibility import PartApplication
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.tests.factories import EmpresaFactory


@pytest.mark.django_db
def test_numero_puertas_disponible_en_formulario():
    empresa = EmpresaFactory(pais="CL", plan="paid")

    form = VehiculoDesarmeForm(empresa=empresa)

    assert "numero_puertas" in form.fields
    assert form.fields["numero_puertas"].initial == 4


@pytest.mark.django_db
def test_fecha_extraccion_asigna_bodega_al_guardar():
    empresa = EmpresaFactory(pais="CL", plan="paid")
    vehiculo = VehiculoDesarme.objects.create(empresa=empresa, patente="MAP-001")

    pieza = PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="ALT-001",
        nombre="Alternador",
        fecha_extraccion=date.today(),
    )

    assert pieza.ubicacion_tipo == "BODEGA"


@pytest.mark.django_db
def test_api_mapa_incluye_piezas_del_vehiculo_y_externas_compatibles():
    empresa = EmpresaFactory(pais="CL", plan="paid", moneda="CLP")
    vehiculo = VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="MAP-002",
        marca_texto="Toyota",
        modelo_texto="Corolla",
        anio=2020,
        tipo_carroceria="sedan",
        numero_puertas=4,
        ubicacion_fisica="Patio Fila 2",
    )
    PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="CAR-02",
        nombre="Puerta delantera izquierda",
        visual_slot="door.front.left",
        precio_venta_sugerido=Decimal("85000"),
    )
    placeholder = VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="SLT-MAP-001",
        es_placeholder=True,
        marca_texto="Proveedor externo",
    )
    PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=placeholder,
        codigo="ALT-002",
        nombre="Alternador 90A",
        origen="COMPRA_EXTERNA",
        ubicacion_tipo="BODEGA",
        ubicacion_fisica="Estante C-2, Repisa 1",
        visual_slot="engine.alternator",
        precio_venta_sugerido=Decimal("85000"),
    )
    PartApplication.objects.create(
        codigo_pieza="ALT-002",
        marca="Toyota",
        modelo="Corolla",
        anio_desde=2019,
        anio_hasta=2022,
    )
    otra_empresa = EmpresaFactory(pais="CL", plan="paid")
    otro_placeholder = VehiculoDesarme.objects.create(
        empresa=otra_empresa,
        patente="SLT-OTRA-001",
        es_placeholder=True,
    )
    PiezaDesarme.objects.create(
        empresa=otra_empresa,
        vehiculo_desarme=otro_placeholder,
        codigo="ALT-002",
        nombre="No debe filtrarse",
        origen="COMPRA_EXTERNA",
    )

    client = Client()
    client.force_login(empresa.user)
    response = client.get(f"/cl/es/desarme/vehiculos/{vehiculo.pk}/api/mapa-piezas/")
    payload = json.loads(response.content)

    assert response.status_code == 200
    assert payload["vehicle"] == {
        "id": vehiculo.pk,
        "body_type": "sedan",
        "doors": 4,
        "yard_location": "Patio Fila 2",
    }
    assert payload["summary"] == {
        "total": 2,
        "mounted": 1,
        "warehouse": 1,
        "sold": 0,
    }
    assert {part["code"] for part in payload["parts"]} == {"CAR-02", "ALT-002"}
    externa = next(part for part in payload["parts"] if part["code"] == "ALT-002")
    assert externa["price"] == 85000
    assert externa["currency"] == "CLP"
    assert externa["origin"] == "COMPRA_EXTERNA"


@pytest.mark.django_db
def test_detalle_vehiculo_renderiza_mapa_visual():
    empresa = EmpresaFactory(pais="CL", plan="paid")
    vehiculo = VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="MAP-003",
        tipo_carroceria="pickup",
        numero_puertas=2,
    )
    client = Client()
    client.force_login(empresa.user)

    response = client.get(f"/cl/es/desarme/vehiculos/{vehiculo.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="vehiculo-mapa-visual"' in content
    assert f'/desarme/vehiculos/{vehiculo.pk}/api/mapa-piezas/' in content
    assert 'class="visual-viewport doors-2"' in content
    assert 'data-visual-slot="body.rear.tailgate"' in content
