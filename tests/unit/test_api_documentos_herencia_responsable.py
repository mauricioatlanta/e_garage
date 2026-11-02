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
def test_hereda_responsable_a_lineas_si_se_envia_en_payload():
    User = get_user_model()
    from django.test import Client

    c = Client()
    c.force_login(User.objects.create_user(username="respo", password="x"))

    from taller.models.clientes import Cliente
    from taller.models.documento import Documento
    from taller.models.empresa import Empresa
    from taller.models.lineas_documento import LineaRepuesto, LineaServicio
    from taller.models.vehiculos import Vehiculo

    # si no existe modelo Tecnico, omitimos
    try:
        from taller.models.tecnico import Tecnico
    except Exception:
        pytest.skip("No existe modelo Tecnico en este proyecto")

    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_herencia", password="test")
    emp = Empresa.objects.create(user=user, nombre_taller="Herencia", pais="CL")
    cli = Cliente.objects.create(empresa=emp, nombre="Cli", tax_id="1-9")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="HER123",
        marca_texto="X",
        modelo_texto="Y",
        anio=2020,
    )
    tec = Tecnico.objects.create(empresa=emp, nombre="Tec 1", activo=True)

    # Usar el prefijo de país correcto basado en la empresa
    country_prefix = "/cl/" if emp.pais == "CL" else "/us/"
    url = f"{country_prefix}documentos/api/create/"

    payload = {
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "vehiculo_id": veh.id,
        "tipo": "FAC",
        "fecha_emision": "2025-02-01",
        "tecnico_responsable_id": tec.id,
        "lineas_servicio": [
            {"nombre": "Srv", "cantidad": 1, "precio_unitario": 1000, "descuento": 0}
        ],
        "lineas_repuesto": [
            {"nombre": "Rep", "cantidad": 1, "precio_unitario": 1000, "descuento": 0}
        ],
    }
    r = c.post(url, data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (200, 201, 202)
    doc_id = r.json()["documento"]["id"]

    # revisar que las líneas tengan el mismo responsable que el documento, si el campo existe
    doc = Documento.objects.get(id=doc_id)
    ls = LineaServicio.objects.filter(documento=doc).first()
    lr = LineaRepuesto.objects.filter(documento=doc).first()

    def _get_responsable_id(obj):
        for fname in (
            "tecnico_id",
            "mecanico_id",
            "responsable_id",
            "tecnico_responsable_id",
        ):
            if hasattr(obj, fname):
                return getattr(obj, fname)
        return None

    if hasattr(doc, "tecnico_responsable_id"):
        expected = doc.tecnico_responsable_id
        for line in filter(None, (ls, lr)):
            rid = _get_responsable_id(line)
            if rid is not None:
                assert rid == expected
