import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo


@pytest.mark.django_db
def test_lista_vehiculos_requires_login(client):
    url = reverse("chile:vehiculos:lista_vehiculos")

    response = client.get(url)

    assert response.status_code == 302
    assert "next=" in response["Location"]
    assert url in response["Location"]


@pytest.mark.django_db
def test_lista_vehiculos_renders_for_logged_user(client):
    user_model = get_user_model()
    from taller.tests.factories import EmpresaFactory
    empresa = EmpresaFactory(
        nombre_taller="Taller Vehiculos Test",
        pais="CL",
        moneda="CLP",
        zona_horaria="America/Santiago",
    )
    user = empresa.user
    cliente = Cliente.objects.create(
        empresa=empresa,
        nombre="Cliente Vehiculos",
        tax_id="1-9",
    )
    Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST01",
        marca_texto="Toyota",
        modelo_texto="Yaris",
        anio=2024,
    )

    client.force_login(user)
    response = client.get(reverse("chile:vehiculos:lista_vehiculos"))

    assert response.status_code == 200
    assert any(
        template.name and "vehiculo" in template.name
        for template in response.templates
        if template.name
    )
    assert "TEST01" in response.content.decode()
