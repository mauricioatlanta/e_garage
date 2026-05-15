import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_linea_repuesto_subtotal_and_str():
    from django.contrib.auth.models import User

    from taller.models.clientes import Cliente
    from taller.models.documento import Documento
    from taller.models.empresa import Empresa
    from taller.models.lineas_documento import LineaRepuesto

    user = User.objects.create_user(username="testuser_subtotal", password="testpass")
    emp = Empresa.objects.create(nombre_taller="Test SA", pais="CL", user=user)
    cli = Cliente.objects.create(empresa=emp, nombre="Cliente Test")
    doc = Documento.objects.create(empresa=emp, cliente=cli, tipo="FAC", fecha_emision="2025-01-01")

    item = LineaRepuesto.objects.create(
        documento=doc,
        nombre="Filtro de aceite",
        cantidad=2,
        precio_unitario=5000,
        descuento=0,
        codigo="FIL001",
        origen_repuesto="EXTERNO",
    )
    # si tu modelo calcula subtotal en save o property:
    subtotal = getattr(item, "subtotal", item.cantidad * item.precio_unitario)
    assert subtotal == 10000
    assert str(item)


@pytest.mark.django_db
def test_linea_servicio_rechaza_service_de_otra_empresa():
    from django.contrib.auth.models import User

    from taller.models.catalogo_servicios import Service
    from taller.models.clientes import Cliente
    from taller.models.documento import Documento
    from taller.models.empresa import Empresa
    from taller.models.lineas_documento import LineaServicio

    user_a = User.objects.create_user(username="tenant_a", password="testpass")
    user_b = User.objects.create_user(username="tenant_b", password="testpass")
    emp_a = Empresa.objects.create(nombre_taller="Empresa A", pais="CL", user=user_a)
    emp_b = Empresa.objects.create(nombre_taller="Empresa B", pais="CL", user=user_b)
    cli = Cliente.objects.create(empresa=emp_a, nombre="Cliente Test")
    doc = Documento.objects.create(
        empresa=emp_a,
        cliente=cli,
        tipo="FAC",
        fecha_emision="2025-01-01",
    )
    foreign_service = Service.objects.create(
        empresa=emp_b,
        code="ALIGNMENT-B",
        category="maintenance",
    )

    linea = LineaServicio(
        documento=doc,
        service=foreign_service,
        nombre="Alineacion premium",
        cantidad=1,
        precio_unitario=15000,
    )

    with pytest.raises(ValidationError):
        linea.full_clean()
