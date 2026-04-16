import json

import pytest
from django.test import RequestFactory

from taller.clientes.forms import ClienteForm
from taller.clientes.views import obtener_ciudades, obtener_ciudades_usa
from taller.models import Ciudad, Estado
from taller.models.region_ciudad import TallerCiudad, TallerRegion


@pytest.mark.django_db
def test_cliente_form_bootstraps_chile_legacy_locations(empresa_chile):
    TallerCiudad.objects.all().delete()
    TallerRegion.objects.all().delete()

    form = ClienteForm(empresa=empresa_chile)

    assert TallerRegion.objects.exists()
    assert TallerCiudad.objects.exists()
    assert form.fields["region"].queryset.exists()


@pytest.mark.django_db
def test_obtener_ciudades_chile_bootstraps_and_returns_cities(empresa_chile):
    TallerCiudad.objects.all().delete()
    TallerRegion.objects.all().delete()

    factory = RequestFactory()

    seed_request = factory.get("/cl/es/clientes/ajax/ciudades/", {"region_id": "0"})
    seed_request.user = empresa_chile.user
    obtener_ciudades(seed_request)

    region = TallerRegion.objects.first()
    assert region is not None

    request = factory.get("/cl/es/clientes/ajax/ciudades/", {"region_id": str(region.id)})
    request.user = empresa_chile.user
    response = obtener_ciudades(request)
    data = json.loads(response.content)

    assert response.status_code == 200
    assert data
    assert {"id", "nombre"} <= set(data[0].keys())


@pytest.mark.django_db
def test_cliente_form_usa_filters_states_for_company_country(empresa_usa):
    estado_us = Estado.objects.create(nombre="California", codigo="CA", pais="US", sales_tax=7.25)
    Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)

    form = ClienteForm(empresa=empresa_usa)
    state_ids = set(form.fields["estado_usa"].queryset.values_list("id", flat=True))

    assert estado_us.id in state_ids
    assert all(
        pais == "US" for pais in form.fields["estado_usa"].queryset.values_list("pais", flat=True)
    )


@pytest.mark.django_db
def test_obtener_ciudades_usa_returns_cities_for_selected_state(empresa_usa):
    estado = Estado.objects.create(nombre="Georgia", codigo="GA", pais="US", sales_tax=4.00)
    ciudad = Ciudad.objects.create(nombre="Atlanta", estado=estado, sales_tax_local=0.00)

    request = RequestFactory().get(
        "/us/es/clientes/ajax/ciudades_usa/", {"estado_id": str(estado.id)}
    )
    request.user = empresa_usa.user

    response = obtener_ciudades_usa(request)
    data = json.loads(response.content)

    assert response.status_code == 200
    assert data == [{"id": ciudad.id, "nombre": ciudad.nombre}]
