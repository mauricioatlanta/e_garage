import json
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

@pytest.mark.django_db
def test_rounding_two_decimals_totals():
    from taller.models.empresa import Empresa
    from taller.models.clientes import Cliente
    from taller.models.vehiculos import Vehiculo

    user = get_user_model().objects.create_user("round", "x")
    c = Client()
    c.force_login(user)

    emp = Empresa.objects.create(user=user, nombre_taller="R", pais="CL")
    cli = Cliente.objects.create(empresa=emp, nombre="C", tax_id="1-9")
    veh = Vehiculo.objects.create(empresa=emp, cliente=cli, patente="RND123", 
                                  marca_texto="M", modelo_texto="D", anio=2024)

    payload = {
        "empresa_id": emp.id, "cliente_id": cli.id, "vehiculo_id": veh.id,
        "tipo": "FAC", "fecha_emision": "2025-03-01",
        "lineas_servicio": [{"nombre":"Srv","cantidad":1,"precio_unitario":1000.00,"descuento":0.00}],
        "lineas_repuesto": [{"nombre":"Rep","cantidad":1,"precio_unitario":999.00,"descuento":0.00}],
    }
    r = c.post("/cl/documentos/api/create/", data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (200,201), r.content
    d = r.json()["documento"]
    # Verifica 2 decimales, y consistencia total=subtotal+iva
    for k in ("subtotal","iva","total"):
        assert isinstance(d[k], (int,float))
        assert round(d[k], 2) == d[k]
    assert round(d["subtotal"] + d["iva"], 2) == d["total"]
