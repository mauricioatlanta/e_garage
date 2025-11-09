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


def _set_any(cs, mapping):
    """
    Setea el primer campo existente entre los nombres típicos.
    mapping: {"iva": 19} o {"sales_tax": 0.075} etc.
    Devuelve True si seteó algo, False si no existía ningún campo.
    """
    for k, v in mapping.items():
        if hasattr(cs, k):
            setattr(cs, k, v)
            cs.save(update_fields=[k])
            return True
    return False


@pytest.mark.django_db
def test_company_settings_tasa_sobrescribe_fallback():
    # si no existe el modelo CompanySettings, hacemos skip
    try:
        from taller.models.company_settings import CompanySettings
    except Exception:
        pytest.skip("No hay CompanySettings en este proyecto")

    User = get_user_model()
    from django.test import Client

    c = Client()
    c.force_login(User.objects.create_user(username="cfg", password="x"))

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # subtotal base = 15000 + 2*5000 = 25000
    def _mk_emp(pais, tasa_setting):
        from django.contrib.auth.models import User

        user = User.objects.create_user(username=f"user_{pais}", password="test")
        emp = Empresa.objects.create(user=user, nombre_taller=f"EMP-{pais}", pais=pais)
        cs = CompanySettings.objects.create(user=user)
        # Intenta setear porcentaje (si el campo típico existe)
        # probamos primero porcentaje como entero (10 => 10%), luego fracción (0.075 => 7.5%)
        ok = _set_any(
            cs,
            {
                "iva": tasa_setting,
                "iva_porcentaje": tasa_setting,
                "sales_tax": tasa_setting,
                "tax_rate": tasa_setting,
                "tasa_iva": tasa_setting,
            },
        )
        if not ok:
            pytest.skip("CompanySettings no tiene campos de tasa compatibles")

        cli = Cliente.objects.create(empresa=emp, nombre="Cli", tax_id="1-9")
        veh = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente=f"P{pais}123",
            marca_texto="X",
            modelo_texto="Y",
            anio=2021,
        )

        # Usar el prefijo de país correcto basado en la empresa
        country_prefix = "/cl/" if pais == "CL" else "/us/"
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
        r = c.post(url, data=json.dumps(payload), content_type="application/json")
        assert r.status_code in (200, 201), r.content
        return r.json()["documento"]

    # Caso 1: CL con 10% explícito (10 → 0.10)
    d1 = _mk_emp("CL", 10)  # 10%
    assert d1["subtotal"] == 25000.0
    assert d1["iva"] == 2500.0
    assert d1["total"] == 27500.0

    # Caso 2: US con 7.5% fraccional (0.075)
    d2 = _mk_emp("US", 0.075)
    assert d2["subtotal"] == 25000.0
    assert round(d2["iva"], 2) == 1875.0
    assert round(d2["total"], 2) == 26875.0
