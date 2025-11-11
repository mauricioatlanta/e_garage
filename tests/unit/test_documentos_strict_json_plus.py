import json

import pytest

from django.contrib.auth import get_user_model
from django.test import override_settings


@override_settings(
    MIDDLEWARE=[
        m for m in __import__("django.conf").conf.settings.MIDDLEWARE if "country_prefix" not in m
    ]
)
@pytest.mark.django_db
def test_documentos_totales_json_estricto_sin_redirect(client):
    User = get_user_model()
    client.force_login(User.objects.create_user("tester", "x"))

    try:
        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo
    except Exception:
        pytest.skip("Modelos Empresa/Cliente/Vehiculo no disponibles")

    # Empresa CL → IVA esperado 19%
    user = User.objects.create_user("testuser", "test@example.com", "password")
    emp = Empresa.objects.create(user=user, nombre_taller="ACME", pais="CL")
    cli = Cliente.objects.create(empresa=emp, nombre="Cliente CL", tax_id="1-9")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="ABC123",
        marca_texto="M",
        modelo_texto="X",
        anio=2024,
    )

    # Subtotal esperado: 2*1000 + 1*500 = 2500 → IVA 475 → Total 2975
    payload = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "vehiculo_id": veh.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {"nombre": "Srv", "cantidad": 2, "precio_unitario": 1000, "descuento": 0}
        ],
        "lineas_repuesto": [
            {"nombre": "Rep", "cantidad": 1, "precio_unitario": 500, "descuento": 0}
        ],
    }
    r = client.post(
        "/cl/documentos/api/create/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert r.status_code in (200, 201), r.content
    data = r.json()
    assert isinstance(data, dict) and "documento" in data
    doc = data["documento"]

    for k in ("subtotal", "iva", "total"):
        assert k in doc, f"Falta campo {k} en JSON"

    assert doc["subtotal"] == 2500
    assert doc["iva"] in (475, 475.0)  # tolerar int/float
    assert doc["total"] in (2975, 2975.0)
