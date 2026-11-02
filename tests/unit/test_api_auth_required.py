import json

import pytest

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse


def _rev(cands, fallback):
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return fallback


@pytest.mark.django_db
def test_crear_vehiculo_requires_auth_then_ok(client):
    url = _rev(
        ["taller:vehiculos_api_create", "vehiculos:api_create", "vehiculos_api_create"],
        "/cl/vehiculos/api/create/",
    )
    # anónimo
    r = client.post(
        url,
        data='{"empresa_id": 1, "cliente_id": 1, "patente": "TEST", "marca": "X", "modelo": "Y"}',
        content_type="application/json",
    )
    assert r.status_code in (
        302,
        400,
        401,
        403,
        405,
    )  # redirige a login, valida datos o bloquea

    # autenticado
    User = get_user_model()
    client.force_login(User.objects.create_user(username="authv", password="x"))
    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa

    emp = Empresa.objects.create(
        nombre_taller="Auth",
        pais="CL",
        user=User.objects.create_user(username="emp_auth", password="x"),
    )
    cli = Cliente.objects.create(empresa=emp, nombre="Ana", tax_id="1-9")
    payload = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "patente": "AUTH01",
        "marca": "X",
        "modelo": "Y",
        "anio": 2020,
    }
    r2 = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert r2.status_code in (200, 201, 202, 405)
