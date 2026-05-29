import json

import pytest

from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_payload_limite_y_negativos(client, django_user_model=None):
    # Login rápido
    User = django_user_model or get_user_model()
    client.force_login(User.objects.create_user("u", "x"))

    # Import tolerante
    try:
        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo
    except Exception:
        pytest.skip("Modelos Empresa/Cliente/Vehiculo no disponibles")

    # Crear usuario para la empresa
    user = User.objects.create_user("testuser", "test@example.com", "password")
    emp = Empresa.objects.create(user=user, nombre_taller="ACME", pais="CL")
    cli = Cliente.objects.create(empresa=emp, nombre="C", tax_id="1-9")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="LIM001",
        marca_texto="M",
        modelo_texto="D",
        anio=2024,
    )

    def post(data):
        return client.post(
            "/cl/documentos/api/create/",
            data=json.dumps(data),
            content_type="application/json",
        )

    base = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "vehiculo_id": veh.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
    }

    # cantidad = 0 -> 400/422
    r = post(
        {
            **base,
            "lineas_servicio": [
                {"nombre": "Srv", "cantidad": 0, "precio_unitario": 10, "descuento": 0}
            ],
        }
    )
    assert r.status_code in (400, 422)

    # precio negativo -> 400/422
    r = post(
        {
            **base,
            "lineas_repuesto": [
                {"nombre": "Rep", "cantidad": 1, "precio_unitario": -1, "descuento": 0}
            ],
        }
    )
    assert r.status_code in (400, 422)

    # descuento extremo (1 o 100%) -> permitido o rechazado, pero nunca 500
    r = post(
        {
            **base,
            "lineas_servicio": [
                {
                    "nombre": "Srv",
                    "cantidad": 1,
                    "precio_unitario": 1000,
                    "descuento": 1,
                }
            ],
        }
    )
    assert r.status_code in (200, 201, 400, 422)
    if r.status_code in (200, 201):
        d = r.json()["documento"]
        assert d["subtotal"] >= 0 and d["iva"] >= 0 and d["total"] >= 0
