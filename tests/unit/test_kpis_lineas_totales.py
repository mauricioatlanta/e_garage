from datetime import datetime

import pytest

from django.contrib.auth import get_user_model
from django.db.models import DecimalField, ExpressionWrapper, F, Sum


@pytest.mark.django_db
def test_kpi_total_por_fecha_emision_con_expressionwrapper():
    from taller.models.documento import Documento
    from taller.models.empresa import Empresa
    from taller.models.lineas_documento import LineaServicio

    User = get_user_model()
    user = User.objects.create_user(
        username="user_kpi", email="user_kpi@test.com", password="testpass"
    )

    emp = Empresa.objects.create(
        nombre_taller="KPI",
        empresa="KPI",
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

    cliente = Cliente.objects.create(empresa=emp, nombre="Cliente KPI")

    doc = Documento.objects.create(
        empresa=emp, tipo="FAC", fecha_emision="2025-01-15", cliente=cliente
    )

    LineaServicio.objects.create(
        documento=doc, nombre="A", cantidad=2, precio_unitario=1000, descuento=0
    )
    LineaServicio.objects.create(
        documento=doc, nombre="B", cantidad=1, precio_unitario=500, descuento=0
    )

    expr = ExpressionWrapper(F("cantidad") * F("precio_unitario"), output_field=DecimalField())
    agg = LineaServicio.objects.filter(documento__fecha_emision="2025-01-15").aggregate(
        total=Sum(expr)
    )
    assert agg["total"] in (2500, 2500.0)  # 2*1000 + 1*500
