import json

import pytest

from django.contrib.auth import get_user_model
from django.test import override_settings


@override_settings(
    MIDDLEWARE=[
        m
        for m in __import__("django.conf").conf.settings.MIDDLEWARE
        if "country_prefix" not in m
    ]
)
@pytest.mark.django_db
def test_company_settings_precede_country_tax(client):
    # Este test se salta si CompanySettings no existe o no es enlazable.
    User = get_user_model()
    user = User.objects.create_user("owner", "x")
    client.force_login(User.objects.create_user("tester", "x"))

    try:
        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo
    except Exception:
        pytest.skip("Modelos Empresa/Cliente/Vehiculo no disponibles")

    emp = Empresa.objects.create(user=user, nombre_taller="ACME CS", pais="CL")
    cli = Cliente.objects.create(empresa=emp, nombre="C", tax_id="1-9")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="CST001",
        marca_texto="M",
        modelo_texto="X",
        anio=2024,
    )

    # Intentamos importar CompanySettings y setear algún campo de tasa conocido
    try:
        from taller.models.company_settings import CompanySettings
    except Exception:
        pytest.skip("CompanySettings no disponible")

    # Creamos settings asociados de la forma más compatible posible
    cs = CompanySettings()
    # Intentamos vinculación compatible (user o empresa, según exista)
    if hasattr(cs, "empresa"):
        cs.empresa = emp
    elif hasattr(cs, "user"):
        cs.user = user
    else:
        pytest.skip("CompanySettings no tiene FK compatible (empresa/user)")

    # Setear un campo de tasa; el código soporta varios nombres
    set_ok = False
    for field, val in [
        ("iva", 0.07),
        ("iva_porcentaje", 7),
        ("sales_tax", 7),
        ("tax_rate", 0.07),
        ("tasa_iva", 7),
    ]:
        if hasattr(cs, field):
            setattr(cs, field, val)
            set_ok = True
            break
    if not set_ok:
        pytest.skip("CompanySettings sin campos de tasa compatibles")

    cs.save()

    # Subtotal 1000 → con 7% = 70 → total 1070
    payload = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "vehiculo_id": veh.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {"nombre": "Srv", "cantidad": 1, "precio_unitario": 1000, "descuento": 0}
        ],
    }
    r = client.post(
        "/cl/documentos/api/create/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert r.status_code in (200, 201), r.content
    doc = r.json()["documento"]
    assert doc["subtotal"] == 1000
    # Tolerar int/float
    assert doc["iva"] in (70, 70.0)
    assert doc["total"] in (1070, 1070.0)
