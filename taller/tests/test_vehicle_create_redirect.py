import pytest
from django.contrib.auth.models import User

from taller.models.vehiculos import Vehiculo
from taller.tests.factories import ClienteFactory, EmpresaFactory


@pytest.mark.django_db
def test_vehicle_creation_redirects_to_localized_us_list_without_return_url(client):
    user = User.objects.create_user(username="vehicle_creator")
    empresa = EmpresaFactory(user=user, pais="US")
    cliente = ClienteFactory(empresa=empresa)
    client.force_login(user)

    response = client.post(
        "/us/es/vehiculos/crear/",
        {
            "patente": "TEST100",
            "vin": "VIN-TEST-002",
            "anio": "2021",
            "millas": "12000",
            "cliente": str(cliente.pk),
        },
        follow=False,
    )

    assert response.status_code == 302, response.context["form"].errors
    assert response["Location"] == "/us/es/vehiculos/"
    vehiculo = Vehiculo.objects.get(empresa=empresa, vin="VIN-TEST-002")
    assert vehiculo.cliente_id == cliente.pk
    assert vehiculo.marca_id is None
    assert vehiculo.modelo_id is None
