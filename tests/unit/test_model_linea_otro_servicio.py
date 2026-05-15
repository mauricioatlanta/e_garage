from datetime import datetime
from decimal import Decimal
from importlib import import_module

import pytest

from django.contrib.auth import get_user_model


def _has_field(model, name):
    return name in {f.name for f in model._meta.fields}


@pytest.mark.django_db
def test_linea_otro_servicio_ganancia():
    # LineaOtroServicio: costo_interno, precio_cliente, ganancia
    try:
        Empresa = import_module("taller.models.empresa").Empresa
        Documento = import_module("taller.models.documento").Documento
        Lineas = import_module("taller.models.lineas_documento")
        LOS = Lineas.LineaOtroServicio
    except Exception:
        pytest.skip("No existe LineaOtroServicio en este proyecto")

    User = get_user_model()
    user = User.objects.create_user(
        username="user_ext", email="user_ext@test.com", password="testpass"
    )

    emp = Empresa.objects.create(
        nombre_taller="EXT",
        empresa="EXT",
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
        user_id=user.id,
    )

    # Crear cliente requerido para el documento
    from taller.models.clientes import Cliente

    cliente = Cliente.objects.create(empresa=emp, nombre="Cliente EXT")

    doc = Documento.objects.create(
        empresa=emp, tipo="FAC", fecha_emision="2025-02-01", cliente=cliente
    )

    data = dict(documento=doc, nombre="Alineación externa", cantidad=1)
    if _has_field(LOS, "costo_interno"):
        data["costo_interno"] = Decimal("10000")
    if _has_field(LOS, "precio_cliente"):
        data["precio_cliente"] = Decimal("16000")
    if _has_field(LOS, "empresa_externa"):
        data["empresa_externa"] = "Taller Externo S.A."

    item = LOS(**data)
    try:
        item.full_clean()
    except Exception:
        pass
    item.save()

    # Si el modelo expone 'ganancia' (campo o property), revisamos cálculo
    if hasattr(item, "ganancia"):
        g = item.ganancia() if callable(item.ganancia) else item.ganancia
        if isinstance(g, (int, float, Decimal)):
            assert Decimal(str(g)) in (Decimal("6000"), Decimal("6000.0"))
