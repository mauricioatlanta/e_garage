import json
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse, NoReverseMatch

def _rev(cands, fb):
    for n in cands:
        try: 
            return reverse(n)
        except NoReverseMatch: 
            pass
    return fb

@pytest.mark.django_db
def test_tax_values_invalid_fallback():
    try:
        from taller.models.company_settings import CompanySettings
    except Exception:
        pytest.skip("Sin CompanySettings")

    from taller.models.empresa import Empresa
    from taller.models.clientes import Cliente
    from taller.models.vehiculos import Vehiculo
    User = get_user_model()
    c = Client()
    c.force_login(User.objects.create_user("taxbad", "x"))

    def _mk(emp_pais, bad_value):
        from django.contrib.auth.models import User
        user = User.objects.create_user(username=f"user_{emp_pais}", password="test")
        emp = Empresa.objects.create(user=user, nombre_taller=f"E-{emp_pais}", pais=emp_pais)
        
        # Usar el prefijo de país correcto basado en la empresa
        country_prefix = "/cl/" if emp_pais == "CL" else "/us/"
        url = f"{country_prefix}documentos/api/create/"
        
        # Crear CompanySettings con el usuario correcto
        if hasattr(CompanySettings, "empresa"):
            cs = CompanySettings.objects.create(empresa=emp)
        elif hasattr(CompanySettings, "user"):
            cs = CompanySettings.objects.create(user=user)
        else:
            cs = CompanySettings.objects.create()
        
        # Setea un campo cualquiera con valor inválido
        for k in ("iva", "iva_porcentaje", "sales_tax", "tax_rate", "tasa_iva"):
            if hasattr(cs, k):
                setattr(cs, k, bad_value)
                cs.save(update_fields=[k])
                break
        
        cli = Cliente.objects.create(empresa=emp, nombre="C", tax_id="1-9")
        veh = Vehiculo.objects.create(empresa=emp, cliente=cli, patente=f"P{emp_pais}X", 
                                     marca_texto="M", modelo_texto="D", anio=2024)
        
        payload = {
            "empresa_id": emp.id, "cliente_id": cli.id, "vehiculo_id": veh.id,
            "tipo": "FAC", "fecha_emision": "2025-01-01",
            "lineas_servicio": [{"nombre": "S", "cantidad": 1, "precio_unitario": 10000}],
        }
        
        # Crear un cliente separado para cada país y autenticar con el usuario correcto
        c_country = Client()
        c_country.force_login(user)
        
        r = c_country.post(url, data=json.dumps(payload), content_type="application/json")
        assert r.status_code in (200, 201), r.content
        return r.json()["documento"]

    d_cl = _mk("CL", "-5")     # string negativo → fallback 19%
    assert d_cl["subtotal"] == 10000.0 and d_cl["iva"] == 1900.0 and d_cl["total"] == 11900.0
    
    d_us = _mk("US", "abc")    # no convertible → fallback 0%
    assert d_us["subtotal"] == 10000.0 and d_us["iva"] in (0, 0.0) and d_us["total"] == 10000.0
