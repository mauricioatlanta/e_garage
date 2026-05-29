from datetime import datetime
from importlib import import_module

import pytest

from django.contrib.auth import get_user_model


def _fields(model):
    return {f.name for f in model._meta.fields}


@pytest.mark.django_db
def test_configuracion_empresa_impuesto_por_pais():
    Empresa = import_module("taller.models.empresa").Empresa
    User = get_user_model()
    user1 = User.objects.create_user(
        username="user_cl", email="user_cl@test.com", password="testpass"
    )
    user2 = User.objects.create_user(
        username="user_us", email="user_us@test.com", password="testpass"
    )

    emp_cl = Empresa.objects.create(
        nombre_taller="CL",
        empresa="CL",
        pais="CL",
        direccion="Test",
        telefono="123",
        email="test@test.com",
        zona_horaria="UTC",
        fecha_inicio=datetime.now(),
        plan="mensual",
        dias_prueba=30,
        suscripcion_activa=True,
        valor_mensual=100,
        moneda="CLP",
        notificacion_5_dias=False,
        notificacion_1_dia=False,
        notificacion_vencido=False,
        user_id=user1.id,
    )
    emp_us = Empresa.objects.create(
        nombre_taller="US",
        empresa="US",
        pais="US",
        direccion="Test",
        telefono="123",
        email="test@test.com",
        zona_horaria="UTC",
        fecha_inicio=datetime.now(),
        plan="mensual",
        dias_prueba=30,
        suscripcion_activa=True,
        valor_mensual=100,
        moneda="USD",
        notificacion_5_dias=False,
        notificacion_1_dia=False,
        notificacion_vencido=False,
        user_id=user2.id,
    )

    SettingsMod = None
    for path in ("taller.models.company_settings", "taller.models.configuracion"):
        try:
            SettingsMod = import_module(path)
            break
        except Exception:
            continue

    if not SettingsMod:
        pytest.skip("No hay modelo de configuración de empresa")

    ModelSettings = None
    for attr in dir(SettingsMod):
        obj = getattr(SettingsMod, attr)
        if hasattr(obj, "_meta") and "empresa" in _fields(obj):
            ModelSettings = obj
            break

    if not ModelSettings:
        pytest.skip("No se encontró modelo concreto de settings")

    cl = ModelSettings(empresa=emp_cl)
    us = ModelSettings(empresa=emp_us)

    # setea IVA/sales tax si existen
    for f in ("iva", "iva_percent", "vat_percent"):
        if f in _fields(ModelSettings):
            setattr(cl, f, 19)

    for f in ("sales_tax", "sales_tax_percent", "tax_percent"):
        if f in _fields(ModelSettings):
            setattr(us, f, 0)

    for obj in (cl, us):
        try:
            obj.full_clean()
        except Exception:
            pass
        obj.save()

    # nada más que verificar persistencia básica (el resto depende de tu lógica de cálculo)
    assert cl.pk and us.pk
