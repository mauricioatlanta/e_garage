from datetime import date

import pytest
from django.contrib.auth.models import User

from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo
from taller.tests.factories import ClienteFactory, EmpresaFactory
from taller.vehiculos.forms import VehiculoForm


@pytest.mark.django_db
def test_chile_vehicle_form_scopes_and_localizes_color_choices():
    empresa = EmpresaFactory(pais="CL")
    request_path = "/cl/es/vehiculos/crear/"
    from django.test import RequestFactory

    request = RequestFactory().get(request_path)
    request.user = empresa.user
    request.empresa = empresa

    form = VehiculoForm(user=empresa.user, request=request, empresa=empresa, country="CL")
    color_labels = {label for _, label in form.fields["color"].choices}

    assert "Blanco" in color_labels
    assert "White" not in color_labels
    assert set(form.fields["color"].queryset.values_list("country", flat=True)) == {"CL"}


@pytest.mark.django_db
def test_chile_vehicle_creation_saves_record_with_company_customer_and_color(client):
    user = User.objects.create_user(username="chile_vehicle_creator")
    empresa = EmpresaFactory(user=user, pais="CL")
    cliente = ClienteFactory(empresa=empresa)
    marca = Marca.objects.create(nombre="Marca de prueba", country="CL")
    modelo = Modelo.objects.create(nombre="Modelo de prueba", marca=marca, country="CL")
    color = ColorVehiculo.get_colores_para_pais("CL").get(nombre="Blanco")
    client.force_login(user)

    response = client.post(
        "/cl/es/vehiculos/crear/",
        {
            "patente": "PRUEBA-CL-001",
            "vin": "VIN-CHILE-001",
            "anio": str(date.today().year),
            "tipo_uso": Vehiculo.TIPO_USO_CLIENTE,
            "cliente": str(cliente.pk),
            "marca": str(marca.pk),
            "modelo": str(modelo.pk),
            "color": str(color.pk),
        },
        follow=False,
    )

    assert response.status_code == 302, response.context["form"].errors
    vehiculo = Vehiculo.objects.get(empresa=empresa, vin="VIN-CHILE-001")
    assert vehiculo.cliente_id == cliente.pk
    assert vehiculo.marca_id == marca.pk
    assert vehiculo.modelo_id == modelo.pk
    assert vehiculo.color_id == color.pk
