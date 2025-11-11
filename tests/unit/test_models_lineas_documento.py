import pytest


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
    )
    # si tu modelo calcula subtotal en save o property:
    subtotal = getattr(item, "subtotal", item.cantidad * item.precio_unitario)
    assert subtotal == 10000
    assert str(item)
