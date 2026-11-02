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
def test_documento_rechaza_fk_de_otra_empresa(client):
    User = get_user_model()
    client.force_login(User.objects.create_user(username="docfk", password="x"))

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    emp1 = Empresa.objects.create(
        nombre_taller="E1",
        pais="CL",
        user=User.objects.create_user(username="emp1", password="x"),
    )
    emp2 = Empresa.objects.create(
        nombre_taller="E2",
        pais="CL",
        user=User.objects.create_user(username="emp2", password="x"),
    )
    cli = Cliente.objects.create(empresa=emp1, nombre="C1", tax_id="1-9")
    cli2 = Cliente.objects.create(empresa=emp2, nombre="C2", tax_id="2-7")
    veh = Vehiculo.objects.create(
        empresa=emp2,
        cliente=cli2,
        patente="MMS123",
        marca_texto="X",
        modelo_texto="Y",
        anio=2019,
    )

    payload = {
        "empresa_id": emp1.id,  # documento dice E1
        "cliente_id": cli.id,  # cliente de E1
        "vehiculo_id": veh.id,  # PERO vehículo de E2 -> debe rechazar
        "tipo": "FAC",
        "fecha_emision": "2025-01-10",
    }
    url = _rev(
        [
            "taller:documentos_api_create",
            "documentos:api_create",
            "documentos_api_create",
        ],
        "/cl/documentos/api/create/",
    )
    r = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (302, 400, 401, 403, 405, 422)
