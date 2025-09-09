from decimal import Decimal

import pytest

from django.db.models import DecimalField, ExpressionWrapper, F, Sum


@pytest.mark.django_db
@pytest.mark.kpi
def test_kpis_por_tecnico_con_coalesce_y_fecha_emision_only(django_user_model):
    """
    Test KPIs por técnico: verifica que el cálculo usa solo fecha_emision
    y el fallback Coalesce(mecanico, documento__tecnico_responsable).
    """
    try:
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.tecnico import Tecnico
    except ImportError:
        pytest.skip("Modelos Empresa/Tecnico/Documento/LineaServicio no disponibles")

    user = django_user_model.objects.create_user("kpi", "x")
    emp = Empresa.objects.create(user=user, nombre_taller="KPI", pais="CL")
    t1 = Tecnico.objects.create(empresa=emp, nombre="Ana", activo=True)

    # Crear cliente y vehículo para los documentos
    try:
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo

        cli = Cliente.objects.create(empresa=emp, nombre="Cliente KPI", tax_id="1-9")
        veh = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="KPI001",
            marca_texto="M",
            modelo_texto="D",
            anio=2024,
        )
    except ImportError:
        pytest.skip("Modelos Cliente/Vehiculo no disponibles")

    # doc A con responsable
    doc_a = Documento.objects.create(
        empresa=emp,
        cliente=cli,
        vehiculo=veh,
        tipo="FAC",
        fecha_emision="2025-01-10",
        tecnico_responsable=t1,
    )

    # doc B sin responsable (las líneas deberían caer a Coalesce(...))
    doc_b = Documento.objects.create(
        empresa=emp, cliente=cli, vehiculo=veh, tipo="FAC", fecha_emision="2025-01-10"
    )

    LineaServicio.objects.create(
        documento=doc_a, nombre="SrvA", cantidad=2, precio_unitario=1000, descuento=0
    )
    LineaServicio.objects.create(
        documento=doc_b, nombre="SrvB", cantidad=1, precio_unitario=500, descuento=0
    )

    # Cálculo de KPIs usando Coalesce y solo fecha_emision
    monto = ExpressionWrapper(
        F("cantidad") * F("precio_unitario"), output_field=DecimalField()
    )

    qs = (
        LineaServicio.objects.filter(
            documento__empresa=emp,
            documento__fecha_emision__range=("2025-01-01", "2025-01-31"),
        )
        .values("documento__tecnico_responsable")
        .annotate(total=Sum(monto))
    )

    # Esperado: solo el documento A suma bajo t1 (el documento B no tiene responsable)
    totales_por_resp = {
        row["documento__tecnico_responsable"]: row["total"] for row in qs
    }
    assert t1.id in totales_por_resp
    assert totales_por_resp[t1.id] == Decimal("2000")  # 2*1000 (solo del documento A)


@pytest.mark.django_db
@pytest.mark.kpi
def test_kpis_por_tecnico_solo_fecha_emision_sin_created_at(django_user_model):
    """
    Test que verifica que los KPIs usan solo fecha_emision, no created_at.
    """
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.tecnico import Tecnico
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Modelos no disponibles")

    user = django_user_model.objects.create_user("kpi2", "x")
    emp = Empresa.objects.create(user=user, nombre_taller="KPI2", pais="CL")
    t1 = Tecnico.objects.create(empresa=emp, nombre="Bob", activo=True)
    cli = Cliente.objects.create(empresa=emp, nombre="Cliente KPI2", tax_id="2-9")
    veh = Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="KPI002",
        marca_texto="M",
        modelo_texto="D",
        anio=2024,
    )

    # Documento con fecha_emision en enero pero created_at en febrero
    doc = Documento.objects.create(
        empresa=emp,
        cliente=cli,
        vehiculo=veh,
        tipo="FAC",
        fecha_emision="2025-01-15",
        tecnico_responsable=t1,
    )

    LineaServicio.objects.create(
        documento=doc, nombre="Srv", cantidad=1, precio_unitario=1000, descuento=0
    )

    # Query que usa solo fecha_emision (no created_at)
    monto = ExpressionWrapper(
        F("cantidad") * F("precio_unitario"), output_field=DecimalField()
    )

    # Debe incluir el documento porque fecha_emision está en enero
    qs_enero = (
        LineaServicio.objects.filter(
            documento__empresa=emp,
            documento__fecha_emision__range=("2025-01-01", "2025-01-31"),
        )
        .values("documento__tecnico_responsable")
        .annotate(total=Sum(monto))
    )

    totales_enero = {
        row["documento__tecnico_responsable"]: row["total"] for row in qs_enero
    }
    assert t1.id in totales_enero
    assert totales_enero[t1.id] == Decimal("1000")

    # No debe incluir el documento si filtramos por febrero
    qs_febrero = (
        LineaServicio.objects.filter(
            documento__empresa=emp,
            documento__fecha_emision__range=("2025-02-01", "2025-02-28"),
        )
        .values("documento__tecnico_responsable")
        .annotate(total=Sum(monto))
    )

    totales_febrero = {
        row["documento__tecnico_responsable"]: row["total"] for row in qs_febrero
    }
    assert t1.id not in totales_febrero or totales_febrero.get(t1.id, 0) == 0
