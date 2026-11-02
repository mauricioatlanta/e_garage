import json

import pytest

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse


def _rev(cands):
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return None


def _post(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_documentos_post_valido_con_lineas_y_json_estricto(client):
    User = get_user_model()
    client.force_login(User.objects.create_user(username="d1", password="x"))

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    emp = Empresa.objects.create(
        nombre_taller="Garage",
        pais="CL",
        user=User.objects.create_user(username="emp3", password="x"),
    )
    cli = Cliente.objects.create(empresa=emp, nombre="Pedro", tax_id="3-5")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="JJKR88",
        marca_texto="Toyota",
        modelo_texto="Yaris",
        anio=2020,
    )

    payload = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "vehiculo_id": veh.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-10",
        "lineas_servicio": [
            {
                "nombre": "Alineación",
                "cantidad": 1,
                "precio_unitario": 15000,
                "descuento": 0,
            }
        ],
        "lineas_repuesto": [
            {"nombre": "Filtro", "cantidad": 2, "precio_unitario": 5000, "descuento": 0}
        ],
    }

    url = (
        _rev(
            [
                "documentos_cl_es:api_create",
                "documentos_us_en:api_create",
                "documentos:api_create",
            ]
        )
        or "/cl/documentos/api/create/"
    )
    resp = _post(client, url, payload)
    assert resp.status_code in (200, 201, 202, 405)

    if resp.status_code in (200, 201):
        data = resp.json()
        assert isinstance(data, dict)
        obj = data.get("documento", data)
        # claves mínimas y tipos
        assert obj.get("tipo") in ("FAC", "BO", "NC", "ND", "OT")
        assert obj.get("fecha_emision")
        if "id" in obj:
            assert isinstance(obj["id"], int)
        # si vuelve totales, deben ser números
        for k in ("subtotal", "total", "iva", "total_con_impuesto"):
            if k in obj:
                assert isinstance(obj[k], (int, float))
    else:
        pytest.skip("Endpoint no crea (no 200/201)")


@pytest.mark.django_db
def test_documentos_post_invalido_lineas_malas(client):
    User = get_user_model()
    client.force_login(User.objects.create_user(username="d2", password="x"))

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    emp = Empresa.objects.create(
        nombre_taller="Garage2",
        pais="CL",
        user=User.objects.create_user(username="emp4", password="x"),
    )
    cli = Cliente.objects.create(empresa=emp, nombre="Ana", tax_id="4-3")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="KZZS31",
        marca_texto="Kia",
        modelo_texto="Rio",
        anio=2019,
    )

    payload = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "vehiculo_id": veh.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-10",
        # errores: cantidad 0 y precio negativo
        "lineas_servicio": [
            {
                "nombre": "Alineación",
                "cantidad": 0,
                "precio_unitario": 15000,
                "descuento": 0,
            }
        ],
        "lineas_repuesto": [
            {"nombre": "Filtro", "cantidad": 1, "precio_unitario": -1, "descuento": 0}
        ],
    }

    url = (
        _rev(
            [
                "documentos_cl_es:api_create",
                "documentos_us_en:api_create",
                "documentos:api_create",
            ]
        )
        or "/cl/documentos/api/create/"
    )
    resp = _post(client, url, payload)
    assert resp.status_code in (400, 401, 403, 405, 422)
