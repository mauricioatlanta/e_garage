import json

import pytest

from django.urls import NoReverseMatch, reverse


def _rev(cands, fallback):
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return fallback


def _post(c, url, payload):
    return c.post(url, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_totales_cl_19_y_us_0():
    from django.test import Client

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    def _mk(emp_pais):
        from django.contrib.auth.models import User

        user = User.objects.create_user(username=f"user_{emp_pais}", password="test")
        emp = Empresa.objects.create(
            user=user, nombre_taller=f"EMP-{emp_pais}", pais=emp_pais
        )
        cli = Cliente.objects.create(empresa=emp, nombre="Cli", tax_id="1-9")
        veh = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente=f"P{emp_pais}123",
            marca_texto="X",
            modelo_texto="Y",
            anio=2021,
        )

        # Usar el prefijo de país correcto basado en la empresa
        country_prefix = "/cl/" if emp_pais == "CL" else "/us/"
        url = f"{country_prefix}documentos/api/create/"

        # Crear un cliente separado para cada país y autenticar con el usuario correcto
        c = Client()
        c.force_login(user)

        payload = {
            "empresa_id": emp.id,
            "cliente_id": cli.id,
            "vehiculo_id": veh.id,
            "tipo": "FAC",
            "fecha_emision": "2025-01-10",
            "lineas_servicio": [
                {
                    "nombre": "Srv",
                    "cantidad": 1,
                    "precio_unitario": 15000,
                    "descuento": 0,
                }
            ],
            "lineas_repuesto": [
                {
                    "nombre": "Rep",
                    "cantidad": 2,
                    "precio_unitario": 5000,
                    "descuento": 0,
                }
            ],
        }
        r = _post(c, url, payload)
        assert r.status_code in (200, 201, 202), r.content
        return r.json()["documento"]

    doc_cl = _mk("CL")
    doc_us = _mk("US")  # acepta US/USA; si usas "USA", cambia aquí a "USA"

    # subtotal esperado: 15000 + (2*5000) = 25000
    assert doc_cl["subtotal"] == 25000.0
    assert doc_cl["iva"] == 4750.0  # 19%
    assert doc_cl["total"] == 29750.0

    assert doc_us["subtotal"] == 25000.0
    assert doc_us["iva"] in (0, 0.0)  # 0%
    assert doc_us["total"] == 25000.0
